import re

import pandas as pd
from sqlalchemy import select

from auth.models import (
    db,
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
YEAR_COLUMN_RE = re.compile(r"^\d{4}$")

def get_or_create_scenario(
    scenario_name: str,
    session
) -> int:
    scenario_id = session.execute(
        select(Scenario.id)
        .where(Scenario.name == scenario_name)
    ).scalar_one_or_none()

    if scenario_id is not None:
        return scenario_id

    session.add(Scenario(name=scenario_name))
    session.commit()

    return session.execute(
        select(Scenario.id)
        .where(Scenario.name == scenario_name)
    ).scalar_one()


def upsert_tables(df, session):
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
    value_cols = [c for c in df.columns if c.isdigit()]
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
    year_cols = [c for c in df.columns if c.isdigit()]
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


def melt_and_map_values(
    df,
    scenario_id,
    table_map,
    series_map
):
    year_cols = [c for c in df.columns if c.isdigit()]

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
    values_df.to_sql(
        "values",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=10_000
    )

def ensure_scenario_not_exists(scenario_name, session):
    exists = session.execute(
        select(Scenario.id)
        .where(Scenario.name == scenario_name)
    ).scalar_one_or_none()

    if exists is not None:
        raise ValueError(
            f"Scenario '{scenario_name}' already exists. "
            "Delete it before uploading a new one."
        )


def validate_upload_format(upload_format: str) -> str:
    selected_format = (upload_format or "").strip()
    if not selected_format:
        raise ValueError("Please choose an upload format before selecting a file.")

    if selected_format != SUPPORTED_UPLOAD_FORMAT:
        raise ValueError(
            "The selected upload format is not available yet. "
            "Please choose 'Format 1: tableName + seriesName + label + yearly data'."
        )

    return selected_format


def _is_year_column(column_name) -> bool:
    return bool(YEAR_COLUMN_RE.match(str(column_name).strip()))


def _find_blank_rows(series: pd.Series) -> list[int]:
    text_values = series.fillna("").astype(str).str.strip()
    return (text_values.index[text_values.eq("")] + 2).tolist()


def _find_invalid_numeric_rows(series: pd.Series) -> list[int]:
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


from sqlalchemy.orm import sessionmaker


def process_uploaded_csv(
    df,
    scenario_name: str,
    engine
):
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    # df = pd.read_csv(csv_path)
    session = SessionLocal()
    try:
    # with Session() as session:
        ensure_scenario_not_exists(scenario_name, session)
        scenario_id = get_or_create_scenario(scenario_name, session)

        table_map = upsert_tables(df, session)
        series_map = upsert_series(df, table_map, session)
        year_map = upsert_years(df, session)

        values_df = melt_and_map_values(
            df, scenario_id, table_map, series_map
        )

        bulk_insert_values(values_df, engine)
    finally:
        session.close()


