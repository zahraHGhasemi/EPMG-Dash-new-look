from auth.models import db, Table, Scenario, Series, Value, Year
# from utils.config_loader import chartsTitle, seriesTitle
import pandas as pd

from sqlalchemy import select

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
        select(Series.name, Series.table_id, Series.id)
    ).all()

    existing_map = {
        (name, table_id): id_
        for name, table_id, id_ in existing
    }

    missing = []
    for table_name, series_name in pairs:
        table_id = table_map[table_name]
        key = (series_name, table_id)
        if key not in existing_map:
            missing.append({
                "name": series_name,
                "title": series_name,  # placeholder
                "table_id": table_id
            })

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
        session.close


