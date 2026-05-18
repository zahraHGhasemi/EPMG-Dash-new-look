import json
import re
from pathlib import Path

from flask import flash
import pandas as pd
from sqlalchemy import delete, select
from auth.models import (
    Study,
    Table,
    Scenario,
    Series,
    Value,
    Year,
    normalize_series_color,
    pastel_continuous_palette,
    next_available_series_color,
)
REQUIRED_UPLOAD_COLUMNS = ("tableName", "seriesName", "label")
SUPPORTED_UPLOAD_FORMAT = "table-series-year"
TABLE_UPLOAD_FORMAT = "table-raw-by-table"
YEAR_COLUMN_RE = re.compile(r"^\d{4}$")
TABLE_INFO_PATH = Path(__file__).resolve().parents[1] / "config" / "table_info.json"

def get_or_create_scenario(
    scenario_name: str,
    session,
    study_id = None
) -> int:
    """Get the ID of an existing scenario by name and study_id, or create it if it doesn't exist."""
    scenario_id = session.execute(
        select(Scenario.id)
        .where(Scenario.name == scenario_name, Scenario.study_id == study_id)
    ).scalar_one_or_none()

    if scenario_id is not None:
        return scenario_id

    session.add(Scenario(name=scenario_name, study_id=study_id))
    session.commit()

    return session.execute(
        select(Scenario.id)
        .where(Scenario.name == scenario_name, Scenario.study_id == study_id)
    ).scalar_one()


def upsert_tables(df, session):
    """Upsert tables based on unique tableName values in the DataFrame, returning a mapping of tableName to table_id."""
    table_names = df["tableName"].unique().tolist()

    existing = session.execute(
        select(Table.name, Table.id)
        .where(Table.name.in_(table_names))
    ).all()

    existing_map = dict(existing)

    missing = [
        {
            "name": name,
            "title": name,  # placeholder for now
            "category": name[:3],
            "label": df.loc[df["tableName"] == name, "label"].iloc[0],
        }
        for name in table_names
        if name not in existing_map
    ]

    if missing:
        session.bulk_insert_mappings(Table, missing)
        session.commit()

    rows = session.execute(
        select(Table.name, Table.id)
        .where(Table.name.in_(table_names))
    ).all()

    return dict(rows)  # tableName → table_id


def upsert_series(df, table_map, session):
    """Upsert series based on unique (seriesName, table_id) pairs in the DataFrame, returning a mapping of (seriesName, table_id) to series_id."""
    pairs = (
        df[["tableName", "seriesName"]]
        .drop_duplicates()
        .values.tolist()
    )

    existing = session.execute(
        select(Series.name, Series.table_id, Series.id, Series.color)
    ).all()

    existing_map = {
        (name, table_id): id_
        for name, table_id, id_, _ in existing
    }
    used_colors_by_table = {}
    for _, table_id, _, color in existing:
        normalized = normalize_series_color(color)
        if normalized:
            used_colors_by_table.setdefault(table_id, set()).add(normalized)

    missing = []
    missing_by_table = {}
    for table_name, series_name in pairs:
        table_id = table_map[table_name]
        key = (series_name, table_id)
        if key not in existing_map:
            row = {
                "name": series_name,
                "title": series_name,  # placeholder
                "table_id": table_id,
            }
            missing.append(row)
            missing_by_table.setdefault(table_id, []).append(row)

    for table_id, rows_for_table in missing_by_table.items():
        used_colors = used_colors_by_table.setdefault(table_id, set())

        if not used_colors:
            palette = pastel_continuous_palette(len(rows_for_table))
            for row, color in zip(rows_for_table, palette):
                row["color"] = color
                used_colors.add(color)
            continue

        for row in rows_for_table:
            new_color = next_available_series_color(used_colors)
            row["color"] = new_color
            used_colors.add(new_color)

    if missing:
        session.bulk_insert_mappings(Series, missing)
        session.commit()

    rows = session.execute(
        select(Series.name, Series.table_id, Series.id)
    ).all()

    return {
        (name, table_id): id_
        for name, table_id, id_ in rows
    }


def prepare_values_df(df, series_objs, scenario_id):
    """Prepare long-format DataFrame for Values table"""
    value_cols = [c for c in df.columns if str(c).isdigit()]
    df_long = df.melt(
        id_vars=['tableName', 'seriesName', 'label'],
        value_vars=value_cols,
        var_name='year',
        value_name='value'
    )
    # Map series_id and scenario_id
    df_long['series_id'] = df_long.apply(lambda row: series_objs[(row['tableName'], row['seriesName'])].id, axis=1)
    df_long['scenario_id'] = scenario_id
    # Keep only columns needed for Values
    df_long = df_long[['scenario_id', 'series_id', 'year', 'value']]
    return df_long

def upsert_years(df, session):
    """Ensure all years in the DataFrame exist in the Year table, inserting any that are missing. Returns a mapping of year to year_id."""
    year_cols = [c for c in df.columns if str(c).isdigit()]
    years = sorted(int(y) for y in year_cols)

    existing = session.execute(
        select(Year.year)
        .where(Year.year.in_(years))
    ).scalars().all()

    existing_set = set(existing)

    missing = [{"year": y} for y in years if y not in existing_set]

    if missing:
        session.bulk_insert_mappings(Year, missing)
        session.commit()

    # year maps to itself
    return {y: y for y in years}


def upsert_year_values(years, session):
    """Ensure all given year values exist in the Year table."""
    cleaned_years = sorted({int(year) for year in years})
    if not cleaned_years:
        return {}

    existing = session.execute(
        select(Year.year)
        .where(Year.year.in_(cleaned_years))
    ).scalars().all()

    existing_set = set(existing)
    missing = [{"year": year} for year in cleaned_years if year not in existing_set]

    if missing:
        session.bulk_insert_mappings(Year, missing)
        session.commit()

    return {year: year for year in cleaned_years}


def melt_and_map_values(
    df,
    scenario_id,
    table_map,
    series_map
):
    """Convert the wide-format DataFrame into long format suitable for bulk insertion into the Values table, mapping tableName and seriesName to their respective IDs."""
    year_cols = [c for c in df.columns if str(c).isdigit()]
    
    melted = df.melt(
        id_vars=["tableName", "seriesName"],
        value_vars=year_cols,
        var_name="year",
        value_name="value"
    )

    melted["table_id"] = melted["tableName"].map(table_map)

    melted["series_id"] = melted.apply(
        lambda r: series_map[(r["seriesName"], r["table_id"])],
        axis=1
    )

    melted["year"] = melted["year"].astype(int)
    melted["scenario_id"] = scenario_id
    return melted[[
        "scenario_id", "series_id", "year", "value"
    ]]

def bulk_insert_values(values_df, engine):
    """Insert the prepared values DataFrame into the Values table using bulk insertion."""
    values_df.to_sql(
        "values",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=10_000
    )


def map_processed_table_upload_values(data, scenario_id_map, table_map, series_map):
    """Map preprocessed Format 2 long data directly to rows for the values table."""
    values_df = data.copy()
    values_df["scenario_id"] = values_df["scenario"].map(scenario_id_map)
    values_df["table_id"] = values_df["tableName"].map(table_map)
    values_df["series_id"] = values_df.apply(
        lambda row: series_map[(row["seriesName"], row["table_id"])],
        axis=1,
    )
    values_df["year"] = values_df["year"].astype(int)
    values_df["value"] = values_df["total"]
    return values_df[["scenario_id", "series_id", "year", "value"]]


def ensure_scenario_not_exists(scenario_name, study_id, session):
    """Check if a scenario with the given name already exists, and raise an error if it does."""
    exists = session.execute(
        select(Scenario.id)
        .where(Scenario.name == scenario_name)
        .where(Scenario.study_id == study_id)
    ).scalar_one_or_none()
    study_name = session.execute(
        select(Study.name).where(Study.id == study_id)
    ).scalar_one_or_none()
    if exists is not None:
        raise ValueError(
            f"Scenario '{scenario_name}' already exists in study {study_name}. "
            "Tick the 'Overwrite existing scenarios' checkbox to replace it."
        )


def get_existing_table_conflicts(session, scenario_names, table_names, study_id=None) -> dict[str, list[str]]:
    """Check if any of the given scenario names already exist with any of the given table names, and return a mapping of scenario name to list of conflicting table names."""
    cleaned_scenarios = sorted({str(name).strip() for name in scenario_names if str(name).strip()})
    cleaned_tables = sorted({str(name).strip() for name in table_names if str(name).strip()})
    if not cleaned_scenarios or not cleaned_tables:
        return {}

    query = (
        select(Scenario.name, Table.name)
        .join(Value, Value.scenario_id == Scenario.id)
        .join(Series, Series.id == Value.series_id)
        .join(Table, Table.id == Series.table_id)
        .where(
            Scenario.name.in_(cleaned_scenarios),
            Table.name.in_(cleaned_tables),
        )
        .distinct()
    )
    if study_id is not None:
        query = query.where(Scenario.study_id == study_id)

    rows = session.execute(query).all()

    conflicts: dict[str, list[str]] = {}
    for scenario_name, table_name in rows:
        conflicts.setdefault(scenario_name, []).append(table_name)

    return {
        scenario_name: sorted(table_list)
        for scenario_name, table_list in conflicts.items()
    }


def format_table_conflicts(conflicts: dict[str, list[str]]) -> str:
    """Format the scenario-to-table conflict mapping into a user-friendly string message."""
    parts = [
        f"{scenario_name}: {', '.join(table_names)}"
        for scenario_name, table_names in sorted(conflicts.items())
    ]
    return "; ".join(parts)


def delete_existing_values_for_scenario_tables(session, scenario_name: str, study_id: int, table_names: list[str], all_tables: bool = False) -> None:
    """Delete existing values for the given scenario name and table names to prevent conflicts with new uploads."""
    cleaned_tables = sorted({str(name).strip() for name in table_names if str(name).strip()})
    scenario_id = session.execute(
        select(Scenario.id).where(Scenario.name == scenario_name, Scenario.study_id == study_id)
    ).scalar_one_or_none()
    print("in delete")
    if scenario_id is None:
        print("scenario not found, nothing to delete")
        return
    if all_tables:
        
        print("in delete all tables for scenario")
        scenario_obj = (
            session.query(Scenario)
            .filter_by(id=scenario_id)
            .first()
        )
        if scenario_obj:
            session.delete(scenario_obj)
            session.commit()
        
        return
    if not cleaned_tables:
        return
    series_ids_subquery = (
        select(Series.id)
        .join(Table, Table.id == Series.table_id)
        .where(Table.name.in_(cleaned_tables))
    )
    session.execute(
        delete(Value).where(
            Value.scenario_id == scenario_id,
            Value.series_id.in_(series_ids_subquery),
        )
    )
    session.commit()
    print(f"Deleted values for scenario '{scenario_name}' and tables {cleaned_tables}")

def load_table_upload_rules() -> dict:
    """Load the table upload rules from the JSON file, returning an empty dict if the file does not exist or is invalid."""
    try:
        with TABLE_INFO_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_table_upload_rules(rules: dict) -> None:
    """Save the table upload rules to the JSON file, overwriting any existing content."""
    with TABLE_INFO_PATH.open("w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
        f.write("\n")


def get_table_upload_options() -> list[str]:
    """Fetch the list of available table names for Format 2 uploads from the table upload rules."""
    return sorted(load_table_upload_rules().keys())


def get_source_table_options() -> list[str]:
    """Fetch the list of unique source table names across all table upload rules, which can be used to inform users about required tables for their selected upload."""
    rules = load_table_upload_rules()
    source_tables = {
        source_table_name
        for table_config in rules.values()
        for source_table_name in table_config.keys()
    }
    return sorted(source_tables)


def get_table_upload_source_map() -> dict[str, list[str]]:
    """Fetch a mapping of table names to their required source tables based on the table upload rules, which can be used to inform users about required tables for their selected upload."""
    rules = load_table_upload_rules()
    return {
        table_name: sorted(table_config.keys())
        for table_name, table_config in rules.items()
    }


def add_table_upload_rule(
    *,
    table_name: str,
    source_name: str,
    keep_dimensions: str,
    default_unit: str,
    aggregation: str,
    filter_column: str | None = None,
    filter_values_text: str | None = None,
    reverse_sign: bool = False,
    cumulate: bool = False,
) -> str:
    """Add a new table upload rule to the table upload rules JSON file, validating inputs and ensuring no conflicts with existing rules.
     Returns the normalized table name of the newly added rule."""
    normalized_table_name = (table_name or "").strip()
    normalized_source_name = (source_name or "").strip()
    normalized_keep_dimensions = (keep_dimensions or "").strip()
    normalized_default_unit = (default_unit or "").strip()
    normalized_aggregation = (aggregation or "").strip()
    normalized_filter_column = (filter_column or "").strip()
    normalized_filter_values_text = (filter_values_text or "").strip()

    if not normalized_table_name:
        raise ValueError("New tableName is required.")
    if not normalized_source_name:
        raise ValueError("source name is required.")
    if not normalized_keep_dimensions:
        raise ValueError("keepDimensions is required.")
    if not normalized_default_unit:
        raise ValueError("defaultUnit is required.")
    if not normalized_aggregation:
        raise ValueError("aggregation is required.")

    rules = load_table_upload_rules()
    if normalized_table_name in rules:
        raise ValueError(
            f"tableName '{normalized_table_name}' already exists in table_info. "
            "Please choose a new name."
        )

    if bool(normalized_filter_column) != bool(normalized_filter_values_text):
        raise ValueError("Both filter column and filter values are required when adding a filter.")

    table_rule = {
        "aggregation": normalized_aggregation,
        "defaultUnit": normalized_default_unit,
        "keepDimensions": normalized_keep_dimensions,
    }

    if normalized_filter_column:
        filter_values = [
            value.strip()
            for value in re.split(r"[\r\n,]+", normalized_filter_values_text)
            if value.strip()
        ]
        if not filter_values:
            raise ValueError("Filter values cannot be empty.")
        table_rule["filter"] = {normalized_filter_column: filter_values}

    if reverse_sign:
        table_rule["reverseSign"] = True
    if cumulate:
        table_rule["cumulate"] = True

    rules[normalized_table_name] = {
        normalized_source_name: table_rule
    }
    save_table_upload_rules(rules)
    return normalized_table_name


def validate_upload_format(upload_format: str) -> str:
    """Validate the selected upload format against supported formats, ensuring a valid selection is made before proceeding with file uploads."""
    selected_format = (upload_format or "").strip()
    if not selected_format:
        raise ValueError("Please choose an upload format before selecting a file.")

    if selected_format not in {SUPPORTED_UPLOAD_FORMAT, TABLE_UPLOAD_FORMAT}:
        raise ValueError(
            "The selected upload format is not available. "
            "Please choose one of the listed upload formats."
        )

    return selected_format


def validate_table_upload_selection(table_name: str) -> str:
    """Validate the selected table name for Format 2 upload against the available table upload rules, ensuring a valid selection is made before proceeding with file uploads."""
    rules = load_table_upload_rules()
    selected_table_name = (table_name or "").strip()
    if not selected_table_name:
        raise ValueError("Please choose a table for Format 2 upload.")

    if selected_table_name not in rules:
        raise ValueError(f"'{selected_table_name}' is not a supported Format 2 table.")

    return selected_table_name


def validate_table_upload_selections(table_names) -> list[str]:
    """Validate the selected table names for Format 2 upload against the available table upload rules, ensuring valid selections are made before proceeding with file uploads."""
    if not table_names:
        raise ValueError("Please choose at least one table for Format 2 upload.")

    rules = load_table_upload_rules()
    cleaned_names = []
    seen = set()
    for table_name in table_names:
        normalized = str(table_name).strip()
        if not normalized or normalized in seen:
            continue
        if normalized not in rules:
            raise ValueError(f"'{normalized}' is not a supported Format 2 table.")
        seen.add(normalized)
        cleaned_names.append(normalized)

    if not cleaned_names:
        raise ValueError("Please choose at least one table for Format 2 upload.")

    return cleaned_names


def get_required_source_tables_for_selection(table_names) -> list[str]:
    """Given a list of selected table names for Format 2 upload, return a sorted list of unique source table names that are required based on the table upload rules, which can be used to inform users about necessary tables for their upload."""
    rules = load_table_upload_rules()
    selected_table_names = validate_table_upload_selections(table_names)
    source_tables = {
        source_table_name
        for table_name in selected_table_names
        for source_table_name in rules[table_name].keys()
    }
    return sorted(source_tables)


def _is_year_column(column_name) -> bool:
    """Determine if a given column name matches the expected format for year columns (4-digit numeric), which is used to validate uploaded DataFrames."""
    return bool(YEAR_COLUMN_RE.match(str(column_name).strip()))


def _find_blank_rows(series: pd.Series) -> list[int]:
    """Identify rows in the given Series that are blank (empty or whitespace), returning a list of their 1-based row numbers for user-friendly error reporting."""
    text_values = series.fillna("").astype(str).str.strip()
    return (text_values.index[text_values.eq("")] + 2).tolist()


def _find_invalid_numeric_rows(series: pd.Series) -> list[int]:
    """Identify rows in the given Series that contain non-numeric values (ignoring blanks), returning a list of their 1-based row numbers for user-friendly error reporting."""
    text_values = series.fillna("").astype(str).str.strip()
    numeric_values = pd.to_numeric(text_values, errors="coerce")
    invalid_mask = text_values.ne("") & numeric_values.isna()
    return (text_values.index[invalid_mask] + 2).tolist()


def _format_row_numbers(row_numbers: list[int]) -> str:
    joined = ", ".join(str(row) for row in row_numbers[:5])
    suffix = "..." if len(row_numbers) > 5 else ""
    return f"{joined}{suffix}"


def validate_uploaded_dataframe(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    if df.empty:
        raise ValueError(f"'{filename}' is empty. Please upload a CSV file with data rows.")

    columns = [str(col).strip() for col in df.columns]
    df = df.copy()
    df.columns = columns

    duplicate_columns = sorted({col for col in columns if columns.count(col) > 1})
    if duplicate_columns:
        joined = ", ".join(duplicate_columns)
        raise ValueError(f"'{filename}' has duplicate column names: {joined}.")

    missing_columns = [col for col in REQUIRED_UPLOAD_COLUMNS if col not in columns]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValueError(f"'{filename}' is missing required column(s): {joined}.")

    year_columns = [col for col in columns if _is_year_column(col)]
    if not year_columns:
        raise ValueError(
            f"'{filename}' must include at least one yearly data column such as 2018 or 2050."
        )

    unexpected_columns = [
        col for col in columns if col not in REQUIRED_UPLOAD_COLUMNS and col not in year_columns
    ]
    if unexpected_columns:
        joined = ", ".join(unexpected_columns)
        raise ValueError(
            f"'{filename}' has invalid column(s): {joined}. "
            "Only tableName, seriesName, label, and 4-digit year columns are allowed."
        )

    for column in REQUIRED_UPLOAD_COLUMNS:
        blank_rows = _find_blank_rows(df[column])
        if blank_rows:
            raise ValueError(
                f"'{filename}' has blank values in '{column}' at CSV row(s): "
                f"{_format_row_numbers(blank_rows)}."
            )

    for year_column in year_columns:
        blank_rows = _find_blank_rows(df[year_column])
        if blank_rows:
            raise ValueError(
                f"'{filename}' has empty values in yearly column '{year_column}' at CSV row(s): "
                f"{_format_row_numbers(blank_rows)}."
            )

        invalid_rows = _find_invalid_numeric_rows(df[year_column])
        if invalid_rows:
            raise ValueError(
                f"'{filename}' has non-numeric values in yearly column '{year_column}' "
                f"at CSV row(s): {_format_row_numbers(invalid_rows)}."
            )

    return df


def get_uploaded_table_names(df: pd.DataFrame) -> list[str]:
    """Return sorted table names present in a validated Format 1 upload."""
    if "tableName" not in df.columns:
        return []
    return sorted({str(name).strip() for name in df["tableName"] if str(name).strip()})


def load_and_validate_uploaded_csvs(files) -> pd.DataFrame:
    validated_frames = []

    for file in files:
        filename = (getattr(file, "filename", "") or "uploaded file").strip()
        if not filename.lower().endswith(".csv"):
            raise ValueError(f"'{filename}' is not a CSV file. Please upload files ending in .csv.")

        try:
            df = pd.read_csv(file.stream)
        except pd.errors.EmptyDataError as exc:
            raise ValueError(f"'{filename}' is empty. Please upload a CSV file with data rows.") from exc
        except pd.errors.ParserError as exc:
            raise ValueError(
                f"'{filename}' could not be read as a CSV file. Please check the file format."
            ) from exc

        validated_frames.append(validate_uploaded_dataframe(df, filename))

    if not validated_frames:
        raise ValueError("At least one CSV file is required.")

    return pd.concat(validated_frames, ignore_index=True)


# def load_single_csv_file(files, *, context_label: str) -> pd.DataFrame:
#     if not files:
#         raise ValueError("At least one CSV file is required.")

#     if len(files) != 1:
#         raise ValueError(f"{context_label} accepts only one CSV file. Please upload a single file.")

#     file = files[0]
#     filename = (getattr(file, "filename", "") or "uploaded file").strip()
#     if not filename.lower().endswith(".csv"):
#         raise ValueError(f"'{filename}' is not a CSV file. Please upload a file ending in .csv.")

#     try:
#         df = pd.read_csv(file.stream)
#     except pd.errors.EmptyDataError as exc:
#         raise ValueError(f"'{filename}' is empty. Please upload a CSV file with data rows.") from exc
#     except pd.errors.ParserError as exc:
#         raise ValueError(
#             f"'{filename}' could not be read as a CSV file. Please check the file format."
#         ) from exc

#     if df.empty:
#         raise ValueError(f"'{filename}' is empty. Please upload a CSV file with data rows.")

#     cleaned_columns = [str(col).strip() for col in df.columns]
#     duplicate_columns = sorted({col for col in cleaned_columns if cleaned_columns.count(col) > 1})
#     if duplicate_columns:
#         joined = ", ".join(duplicate_columns)
#         raise ValueError(f"'{filename}' has duplicate column names: {joined}.")

#     df = df.copy()
#     df.columns = cleaned_columns
#     return df


def load_source_csv_files(files, required_source_tables: list[str]) -> dict[str, tuple[pd.DataFrame, str]]:
    if not files:
        raise ValueError("At least one CSV file is required.")

    required_sources = sorted({source.strip() for source in required_source_tables if source.strip()})
    if not required_sources:
        raise ValueError("No source CSV files are required for the selected tables.")

    loaded_files: dict[str, tuple[pd.DataFrame, str]] = {}

    for file in files:
        filename = (getattr(file, "filename", "") or "uploaded file").strip()
        if not filename.lower().endswith(".csv"):
            raise ValueError(f"'{filename}' is not a CSV file. Please upload a file ending in .csv.")

        source_name = Path(filename).stem.strip()
        if source_name in loaded_files:
            raise ValueError(
                f"Duplicate source file '{source_name}.csv' detected. Please upload each required source file once."
            )

        try:
            df = pd.read_csv(file.stream)
        except pd.errors.EmptyDataError as exc:
            raise ValueError(f"'{filename}' is empty. Please upload a CSV file with data rows.") from exc
        except pd.errors.ParserError as exc:
            raise ValueError(
                f"'{filename}' could not be read as a CSV file. Please check the file format."
            ) from exc

        if df.empty:
            raise ValueError(f"'{filename}' is empty. Please upload a CSV file with data rows.")

        cleaned_columns = [str(col).strip() for col in df.columns]
        duplicate_columns = sorted({col for col in cleaned_columns if cleaned_columns.count(col) > 1})
        if duplicate_columns:
            joined = ", ".join(duplicate_columns)
            raise ValueError(f"'{filename}' has duplicate column names: {joined}.")

        df = df.copy()
        df.columns = cleaned_columns
        loaded_files[source_name] = (df, filename)

    missing_sources = [f"{source}.csv" for source in required_sources if source not in loaded_files]
    if missing_sources:
        raise ValueError(
            "Missing required source CSV file(s): " + ", ".join(missing_sources) + "."
        )

    unexpected_sources = [f"{source}.csv" for source in loaded_files.keys() if source not in required_sources]
    if unexpected_sources:
        raise ValueError(
            "Unexpected source CSV file(s): " + ", ".join(sorted(unexpected_sources)) + "."
        )

    return loaded_files


def validate_table_upload_dataframe(df: pd.DataFrame, table_name: str, filename: str) -> pd.DataFrame:
    selected_table_name = validate_table_upload_selection(table_name)
    rules = load_table_upload_rules()[selected_table_name]

    required_columns = {"Scenario", "Period", "Pv"}
    for source_table_name, rule in rules.items():
        keep_dimension = rule.get("keepDimensions")
        if keep_dimension:
            required_columns.add(keep_dimension)
        for filter_column in rule.get("filter", {}).keys():
            required_columns.add(filter_column)

    missing_columns = [col for col in sorted(required_columns) if col not in df.columns]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValueError(
            f"'{filename}' is missing required Format 2 column(s) for table "
            f"'{selected_table_name}': {joined}."
        )

    for column in required_columns:
        blank_rows = _find_blank_rows(df[column])
        if blank_rows:
            raise ValueError(
                f"'{filename}' has blank values in '{column}' at CSV row(s): "
                f"{_format_row_numbers(blank_rows)}."
            )

    invalid_period_rows = _find_invalid_numeric_rows(df["Period"])
    if invalid_period_rows:
        raise ValueError(
            f"'{filename}' has non-numeric values in 'Period' at CSV row(s): "
            f"{_format_row_numbers(invalid_period_rows)}."
        )

    invalid_value_rows = _find_invalid_numeric_rows(df["Pv"])
    if invalid_value_rows:
        raise ValueError(
            f"'{filename}' has non-numeric values in 'Pv' at CSV row(s): "
            f"{_format_row_numbers(invalid_value_rows)}."
        )

    return df


from sqlalchemy.orm import sessionmaker


def process_uploaded_csv(
    df,
    scenario_name: str,
    engine,
    study_id = None, 
    *,
    allow_existing_scenario: bool = False,
    overwrite_table_names= None,
):
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    # df = pd.read_csv(csv_path)
    session = SessionLocal()
    try:
        # print(allow_existing_scenario, "allow_existing_scenario")
        if not allow_existing_scenario:
            ensure_scenario_not_exists(scenario_name, study_id, session)

        else:
            scenario_id_deleted = session.execute(select(Scenario.id).where(Scenario.name == scenario_name, Scenario.study_id == study_id)).scalar_one_or_none()
            # print(scenario_id_deleted, "scenario_id before deletion")
            delete_existing_values_for_scenario_tables(
                session,
                scenario_name,
                study_id,
                table_names=(overwrite_table_names if overwrite_table_names is not None else []),
                all_tables=(allow_existing_scenario and overwrite_table_names == None)
            )
            scenario_id_deleted = session.execute(select(Scenario.id).where(Scenario.name == scenario_name, Scenario.study_id == study_id)).scalar_one_or_none()
            # print(scenario_id_deleted, "scenario_id after deletion")
        scenario_id = get_or_create_scenario(scenario_name, session, study_id=study_id)

        table_map = upsert_tables(df, session)
        series_map = upsert_series(df, table_map, session)
        upsert_years(df, session)

        if allow_existing_scenario and overwrite_table_names:
            delete_existing_values_for_scenario_tables(
                session,
                scenario_name,
                study_id,
                table_names=overwrite_table_names,
                all_tables=(allow_existing_scenario and (len(overwrite_table_names) == 0 or overwrite_table_names ==None))
            )

        values_df = melt_and_map_values(
            df, scenario_id, table_map, series_map
        )

        bulk_insert_values(values_df, engine)
    finally:
        session.close()


def read_data_csv(df, table_rule_map, source_table_name, output_table_name=None):
    if (
        table_rule_map is None
        or source_table_name not in table_rule_map.keys()
        or table_rule_map[source_table_name]["keepDimensions"] is None
    ):
        print(
            "No info found on how to process: {}. It will be skipped.".format(source_table_name)
        )
        return None

    table_name = output_table_name or source_table_name
    rule = table_rule_map[source_table_name]

    df = df.copy()
    df["tableName"] = table_name

    if "Units" not in df.columns:
        if rule["defaultUnit"] is not None:
            df["Units"] = rule["defaultUnit"]
        else:
            df["Units"] = "missing"

    rename_dims_map = {
        "Scenario": "scenario",
        "Period": "year",
        "Region": "region",
        "Pv": "total",
        "Units": "label",
        rule["keepDimensions"]: "seriesName",
    }

    exclude_columns = (
        "UserName",
        "ModelName",
        "Studyname",
        "Attribute",
        "Commodity",
        "Commodityset",
        "Process",
        "Processset",
        "Vintage",
        "Timeslice",
        "Userconstraint",
    )

    # Filter data
    if "filter" in rule.keys():
        for k, v in rule["filter"].items():
            df = df[df[k].isin(v)]

    # Rename some columns
    df.rename(columns=rename_dims_map, inplace=True)

    # Remove columns in excludeColumns
    df = df[[i for i in df.columns if i not in exclude_columns]]

    df = df.groupby([i for i in df.columns if not i == "total"]).agg(
        rule["aggregation"]
    )

    if "reverseSign" in rule.keys():
        if rule["reverseSign"] is True:
            df = -df

    if "cumulate" in rule.keys():
        if rule["cumulate"] is True:
            df = df.unstack(level="year", fill_value=0).stack()
            df['total'] = df.groupby([i for i in df.index.names if not i == "year"])['total'].cumsum()

    return df.reset_index()

# def process_uploaded_csv_by_table_name(table_name, files, engine):
#     return process_uploaded_csv_by_table_names([table_name], files, engine)


def process_uploaded_csv_by_table_names(table_names, study_id, files, engine, *, overwrite_existing_tables: bool = False):
    selected_table_names = validate_table_upload_selections(table_names)
    rules = load_table_upload_rules()
    required_source_tables = get_required_source_tables_for_selection(selected_table_names)
    loaded_source_files = load_source_csv_files(files, required_source_tables)

    data = pd.DataFrame()
    for selected_table_name in selected_table_names:
        for source_table_name, rule in rules[selected_table_name].items():
            raw_df, filename = loaded_source_files[source_table_name]
            validated_df = validate_table_upload_dataframe(raw_df, selected_table_name, filename)
            processed_df = read_data_csv(
                validated_df,
                {source_table_name: rule},
                source_table_name,
                output_table_name=selected_table_name,
            )
            if processed_df is not None and not processed_df.empty:
                data = pd.concat([data, processed_df], ignore_index=True)

    assert len(data.index), "The dataframe is empty. No data has been read."

    data = data.groupby([i for i in data.columns if not i == "total"]).agg("sum")
    data = data.reset_index()
    numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns
    data[numeric_columns] = data[numeric_columns].mask(data[numeric_columns].abs() < 0.000001, 0)
    scenario_names = sorted(data["scenario"].astype(str).str.strip().unique().tolist())

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    session = SessionLocal()
    try:
        conflicts = get_existing_table_conflicts(session, scenario_names, selected_table_names, study_id)
    finally:
        session.close()

    if conflicts and not overwrite_existing_tables:
        raise ValueError(
            "Some selected tables already exist for these scenario(s): "
            f"{format_table_conflicts(conflicts)}. "
            "Tick 'Overwrite existing selected tables' to replace them."
        )

    data = (
        data
        .assign(scenario=data["scenario"].astype(str).str.strip())
        .groupby(["scenario", "tableName", "seriesName", "label", "year"], as_index=False)["total"]
        .sum()
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    session = SessionLocal()
    try:
        for scenario_name in scenario_names:
            delete_existing_values_for_scenario_tables(
                session,
                scenario_name,
                study_id,
                table_names=selected_table_names,
            )

        scenario_id_map = {
            scenario_name: get_or_create_scenario(scenario_name, session, study_id=study_id)
            for scenario_name in scenario_names
        }
        table_map = upsert_tables(data, session)
        series_map = upsert_series(data, table_map, session)
        upsert_year_values(data["year"], session)
        values_df = map_processed_table_upload_values(
            data,
            scenario_id_map,
            table_map,
            series_map,
        )
    finally:
        session.close()

    bulk_insert_values(values_df, engine)

    return scenario_names
