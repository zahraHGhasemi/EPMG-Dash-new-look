
# from utils.config_loader import chartsTitle
# from utils.database_utils import read_sql
# category_dic = { 'Transport': 'TRA',
#                 'Residential': 'RSD',
#                 'Services': 'SRV',
#                 'Industry': 'IND',
#                 'Power': 'PWR',
#                 'Supply': 'SUP',
#                 'Agriculture': 'AGR',
#                 'System': 'SYS'
#                 }
# def get_categories(df_1):
#     query = 'SELECT DISTINCT "cat" FROM observations'
#     df = read_sql(query)
#     return df["cat"].dropna().tolist()


# def get_subcategories(category):
#     category_id = category_dic.get(category, "").lower()
#     query = """
#         SELECT DISTINCT "tableTitle"
#         FROM observations
#         WHERE "cat" = :cat
#     """
#     df = read_sql(query, params={"cat": category_id})
#     return df["tableTitle"].dropna().tolist()

# def get_table_id(table_name, category):
#     category_id = category_dic.get(category, "").lower()
#     query = """
#         SELECT "tableName"
#         FROM observations
#         WHERE "tableTitle" = :tableTitle AND "cat" = :cat
#         LIMIT 1
#     """
#     df = read_sql(query, params={"tableTitle": table_name, "cat": category_id})
#     return df["tableName"].iloc[0] if not df.empty else None
# def get_filtered_df(table_id, scenario, year_range):
#     """Filter observations by tableName, Scenario, and Year range."""
#     query = """
#         SELECT *
#         FROM observations
#         WHERE "tableName" = :tableName
#           AND "Scenario" = :scenario
#           AND "Year" BETWEEN :year_start AND :year_end
#         ORDER BY "seriesName", "Year";
#     """
#     df = read_sql(query, params={
#         "tableName": table_id,
#         "scenario": scenario,
#         "year_start": year_range[0],
#         "year_end": year_range[1]
#     })
#     return df

def get_subcategory_name(subcategory):
    if subcategory in chartsTitle:
        return chartsTitle[subcategory]
    else:
        return subcategory















# def get_categories(df):
#     return df['cat'].unique().tolist()

# def get_subcategories(category):
    
#     category_id = category_dic[category].lower()
    
#     df_filtered = df[df['cat']== category_id]
#     return df_filtered['tableTitle'].unique().tolist()

# def get_table_id(table_name,category):
#     return df[(df['tableTitle'] == table_name) & (df['cat']== category_dic[category].lower())]['tableName'].iloc[0]
   
# def get_filtered_df(table_id, scenario, year_range):
#     filtered_data = all_data_melted[(all_data_melted['tableName'] == table_id)&
#                                     (all_data_melted['Scenario']== scenario)&
#                                     (all_data_melted['Year'] >= year_range[0])&
#                                     (all_data_melted['Year'] <= year_range[1])]
#     return filtered_data




#---------------------------------------------------------------------------------------------------------------------------------------------


from utils.config_loader import chartsTitle
# from utils.database_utils import read_sql
from flask import session, has_request_context
from flask_login import current_user
import pandas as pd
import os
from flask import current_app
from config.constants import CATEGORY_DICT
# Mapping of category names to IDs


# --- Helper to get user uploaded data from session ---
def get_user_df():
    if not has_request_context():
        return None   # 👈 THIS LINE FIXES YOUR ERROR

    meta = session.get("user_scenario")
    if not meta:
        return None

    path = os.path.join(
        current_app.instance_path,
        "user_uploads",
        f"{meta['id']}.parquet"
    )

    if not os.path.exists(path):
        return None

    return pd.read_parquet(path, engine="pyarrow")

# --- Functions with optional df_override ---
# from flask import has_request_context
# from utils.database_utils import read_sql
# from utils.get_data import get_user_df


# def get_scenarios(df_override=None):
#     """
#     Returns sorted list of scenarios.
#     - If df_override is provided → use it
#     - Else → read from database
#     """
#     # 🔹 Case 1: Explicit dataframe provided
#     if df_override is not None:
#         if df_override.empty:
#             return []
#         return sorted(df_override["Scenario"].dropna().unique().tolist())

#     # 🔹 Case 2: Auto-detect user session (user dash)
#     if has_request_context():
#         df_user = get_user_df()
#         if df_user is not None and not df_user.empty:
#             return sorted(df_user["Scenario"].dropna().unique().tolist())

#     # 🔹 Case 3: Default → database
#     query = 'SELECT DISTINCT "Scenario" FROM observations ORDER BY "Scenario"'
#     df = read_sql(query)
#     return sorted(df["Scenario"].dropna().unique().tolist())


# def get_categories(df_override=None):
#     df = df_override if df_override is not None else read_sql('SELECT DISTINCT "cat" FROM observations')
#     return df["cat"].dropna().unique().tolist()


# def get_subcategories(category, df_override=None):
#     df = df_override[df_override['cat'] == category] if df_override is not None else read_sql(
#         """
#         SELECT DISTINCT "tableTitle"
#         FROM observations
#         WHERE "cat" = :cat
#         """,
#         params={"cat": category}
#     )

#     return df["tableTitle"].dropna().unique().tolist()


# def get_table_id(table_name, category, df_override=None):
#     if df_override is not None:
#         # search in dataframe
#         df_filtered = df_override[
#             (df_override["tableTitle"] == table_name) &
#             (df_override["cat"] == category)
#         ]
#         return df_filtered["tableName"].iloc[0] if not df_filtered.empty else None
#     else:
#         df = read_sql(
#             """
#             SELECT "tableName"
#             FROM observations
#             WHERE "tableTitle" = :tableTitle AND "cat" = :cat
#             LIMIT 1
#             """,
#             params={"tableTitle": table_name, "cat": category}
#         )
#         return df["tableName"].iloc[0] if not df.empty else None


# def get_filtered_df(table_id, scenario, year_range, df_override=None):
#     if df_override is not None:
#         df_filtered = df_override[
#             (df_override["tableName"] == table_id) &
#             (df_override["Scenario"] == scenario) &
#             (df_override["Year"] >= year_range[0]) &
#             (df_override["Year"] <= year_range[1])
#         ].sort_values(["seriesName", "Year"])
#         return df_filtered
#     else:
#         query = """
#             SELECT *
#             FROM observations
#             WHERE "tableName" = :tableName
#               AND "Scenario" = :scenario
#               AND "Year" BETWEEN :year_start AND :year_end
#             ORDER BY "seriesName", "Year";
#         """
#         df = read_sql(query, params={
#             "tableName": table_id,
#             "scenario": scenario,
#             "year_start": year_range[0],
#             "year_end": year_range[1]
#         })
#         return df
