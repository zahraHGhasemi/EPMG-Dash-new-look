


# import os
# import pandas as pd
# from sqlalchemy import create_engine, text, inspect
# from sqlalchemy.orm import sessionmaker, declarative_base
# from sqlalchemy.pool import NullPool

# # --- Database connection ---
# DB_URL = os.getenv(
#     "APP_DB_URL",
#     'postgresql+psycopg2://neondb_owner:npg_R7ugMkq3NQFO@ep-fragrant-truth-ab92jg3a-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
# )

# engine = create_engine(DB_URL, 
#                         echo=False, 
#                         # pool_pre_ping=True,
#                         # pool_size=5,
#                         # max_overflow=10,
#                         # pool_recycle=300,
#                         poolclass=NullPool
#                     )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # --- Utility functions ---

# def read_sql(query, params=None):
#     """Run a SQL SELECT query and return results as a pandas DataFrame."""
#     with engine.connect() as conn:
#         return pd.read_sql_query(text(query), conn, params=params)


# def execute_sql(statement, params=None):
#     """Run non-SELECT statements like CREATE INDEX, INSERT, UPDATE, etc."""
#     with engine.begin() as conn:
#         conn.execute(text(statement), params or {})


# # def load_data_from_postgres():
# #     """Load the main dataset (replaces previous CSV loading)."""
# #     query = "SELECT * FROM observations"
# #     return read_sql(query)





# # def write_scenario_to_database(df, table_name="observations"):
# #     if df.empty:
# #         return {
# #             "written": [],
# #             "skipped": []
# #         }
# #     inspector = inspect(engine)

# #     db_columns = {col["name"] for col in inspector.get_columns(table_name)}
# #     df = df[[c for c in df.columns if c in db_columns]]

# #     uploaded_scenarios = df["Scenario"].dropna().unique().tolist()
# #     with engine.connect() as conn:
# #         result = conn.execute(
# #             text("""
# #                 SELECT DISTINCT "Scenario"
# #                 FROM observations
# #                 WHERE "Scenario" = ANY(:scenarios)
# #             """),
# #             {"scenarios": uploaded_scenarios}
# #         )
# #         existing_scenarios = {row[0] for row in result}

    
# #     new_scenarios = set(uploaded_scenarios) - existing_scenarios

# #     if not new_scenarios:
# #         return {
# #             "written": [],
# #             "skipped": uploaded_scenarios
# #         }

# #     df_new = df[df["Scenario"].isin(new_scenarios)]

# #     df_new.to_sql(
# #         table_name,
# #         con=engine,
# #         if_exists="append",
# #         index=False,
# #         method="multi",
# #         chunksize=5000
# #     )

# #     return {
# #         "written": sorted(new_scenarios),
# #         "skipped": sorted(existing_scenarios)
# #     }

# # def delete_scenarios_from_database(scenarios: list[str]):
# #     if not scenarios:
# #         return 0

# #     with engine.begin() as conn:
# #         result = conn.execute(
# #             text("""
# #                 DELETE FROM observations
# #                 WHERE "Scenario" = ANY(:scenarios)
# #             """),
# #             {"scenarios": scenarios}
# #         )

# #     return result.rowcount

# from sqlalchemy import inspect

# INSPECTOR = inspect(engine)
# OBSERVATION_COLUMNS = {
#     col["name"] for col in INSPECTOR.get_columns("observations")
# }


# def write_scenario_to_database(
#     df,
#     table_name="observations",
#     seen_scenarios=None
# ):
#     if df.empty:
#         return {"written": [], "skipped": []}

#     if seen_scenarios is None:
#         seen_scenarios = set()

#     # keep only valid DB columns
#     df = df[[c for c in df.columns if c in OBSERVATION_COLUMNS]]

#     uploaded_scenarios = set(
#         df["Scenario"].dropna().unique().tolist()
#     )

#     # remove scenarios already handled in previous chunks
#     uploaded_scenarios -= seen_scenarios

#     if not uploaded_scenarios:
#         return {"written": [], "skipped": []}

#     # check DB only once per new scenario
#     with engine.connect() as conn:
#         result = conn.execute(
#             text("""
#                 SELECT DISTINCT "Scenario"
#                 FROM observations
#                 WHERE "Scenario" = ANY(:scenarios)
#             """),
#             {"scenarios": list(uploaded_scenarios)}
#         )
#         existing_scenarios = {row[0] for row in result}

#     new_scenarios = uploaded_scenarios - existing_scenarios

#     if not new_scenarios:
#         seen_scenarios.update(uploaded_scenarios)
#         return {
#             "written": [],
#             "skipped": sorted(uploaded_scenarios)
#         }

#     df_new = df[df["Scenario"].isin(new_scenarios)]

#     df_new.to_sql(
#         table_name,
#         con=engine,
#         if_exists="append",
#         index=False,
#         method="multi",
#         chunksize=1000   # smaller = safer on Render
#     )

#     seen_scenarios.update(uploaded_scenarios)

#     return {
#         "written": sorted(new_scenarios),
#         "skipped": sorted(existing_scenarios)
#     }
