# utils/db_utils.py
import sqlalchemy

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
import os
import pandas as pd
from utils.dataframe_melter import load_data
# # Configure DB URL via env var for easy switch: default to SQLite file
# DB_URL = os.getenv("APP_DB_URL", "sqlite:///data_new/data.db")  

# # create_engine supports both sqlite and postgresql urls
# engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
DB_URL = os.getenv(
    "APP_DB_URL",
    "postgresql://dash_data_user:2vDoGom9Fee7LlyTIqOfcQW4eU3TI11v@dpg-d3sbvmndiees738bd16g-a.oregon-postgres.render.com/dash_data"
)

engine = create_engine(DB_URL, echo=False)  # echo=True for debug

def read_sql(query, params=None):
    """Return a pandas DataFrame for the given SQL SELECT query."""
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params)

def execute_sql(statement, params=None):
    """Execute a non-SELECT statement (CREATE INDEX, INSERT, UPDATE, etc.)."""
    with engine.begin() as conn:
        conn.execute(text(statement), params or {})

all_data_melted = load_data("data_new/all_data_melted.csv")
df = all_data_melted[['tableName', 'seriesName', 'label', 'Scenario', 'Year', 'Value', 'tableTitle', 'seriesTitle', 'cat']]
# Optional: ensure column names are normalized
df.columns = [c.strip() for c in df.columns]

# Write to SQL (replace existing)
df.to_sql("observations", con=engine, if_exists="replace", index=False)

# Add indexes (fast lookups)
with engine.begin() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_table ON observations (tableName)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_series ON observations (seriesName)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_table_title ON observations (tableTitle)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_series_title ON observations (seriesTitle)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_scenario ON observations (Scenario)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_label ON observations (label)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_year ON observations (Year)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_value ON observations (Value)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_obs_cat ON observations (cat)"))