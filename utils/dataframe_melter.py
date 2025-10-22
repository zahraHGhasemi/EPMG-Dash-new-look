from utils.config_loader import chartsTitle, seriesTitle
import pandas as pd
import numpy as np
from utils.data_loader import load_and_concat_data
import os
from utils.database_utils import read_sql


def add_title_column(df):
    # Merge with chartsTitle to add the complete table name
    df = pd.merge(
        df,
        chartsTitle,
        left_on='tableName',
        right_on='tableName',
        how='left'
    )
    df.rename(columns={0: 'tableTitle'}, inplace=True)

    # Merge with seriesTitle to add the complete series name
    df = pd.merge(
        df,
        seriesTitle,
        left_on='seriesName',
        right_on='seriesName',
        how='left'
    )
    df.rename(columns={0: 'seriesTitle'}, inplace=True)
    df['tableTitle'] = df['tableTitle'].fillna(df['tableName'])
    df['seriesTitle'] = df['seriesTitle'].fillna(df['seriesName'])
    df['tableTitle'] = df['tableTitle'].replace({np.nan: 'nan'})
    df['seriesTitle'] = df['seriesTitle'].replace({np.nan: 'nan'})
    
    return df

def melt_dataframe(all_data_df):
    expected_id_vars = ['tableName', 'seriesName', 'label', 'Scenario']
    id_vars = [col for col in expected_id_vars if col in all_data_df.columns]
    if not all_data_df.empty:
        years = [col for col in all_data_df.columns if col.isdigit()]
    else:
        years = []
    all_data_melted = all_data_df.melt(
        id_vars=id_vars,
        value_vars=years,
        var_name='Year',
        value_name='Value'
    )

    all_data_melted['Year'] = all_data_melted['Year'].astype(int)
    all_data_melted = add_title_column(all_data_melted)
    all_data_melted["category"]= all_data_melted['tableName'].apply(lambda x: x.split("_"))
    all_data_melted['category'] = all_data_melted['category'].apply(
        lambda cat: [c.lower() for c in cat] if isinstance(cat, list) else cat)
    
    all_data_melted["cat"] = all_data_melted['tableName'].apply(lambda x: x[:3].lower())

    
    all_data_melted['Year'] = all_data_melted['Year'].astype('int16')
    all_data_melted['Value'] = all_data_melted['Value'].astype('float32')
    all_data_melted['Scenario'] = all_data_melted['Scenario'].astype('category')
    all_data_melted['seriesName'] = all_data_melted['seriesName'].astype('category')

    scenarios = sorted(all_data_melted['Scenario'].unique())
    return all_data_melted, scenarios




def update_data_melted(all_data_df):
    global all_data_melted, scenarios
    all_data_melted, scenarios = melt_dataframe(all_data_df)
    return all_data_melted, scenarios
def get_data_melted(scenario=[], year_range=[]):
    # filtered_data = all_data_melted     
    # if scenario:
    #     filtered_data = all_data_melted[all_data_melted['Scenario'] == scenario]
    # if year_range:
    #     filtered_data = filtered_data[
    #         (filtered_data['Year'] >= year_range[0]) & (filtered_data['Year'] <= year_range[1])
    #     ]
    # if not scenario and not year_range:
    #     filtered_data = all_data_melted
    # return filtered_data 
    query = 'SELECT * FROM observations WHERE 1=1'
    params = {}

    if scenario:
        query += ' AND "Scenario" = :scenario'
        params['scenario'] = scenario

    if year_range:
        query += ' AND "Year" BETWEEN :start_year AND :end_year'
        params['start_year'] = year_range[0]
        params['end_year'] = year_range[1]

    df = read_sql(query, params=params)
    return df

def get_scenarios():
    # scenarios = sorted(all_data_melted['Scenario'].unique())
    # return scenarios
    query = 'SELECT DISTINCT "Scenario" FROM observations ORDER BY "Scenario"'
    df = read_sql(query)
    return sorted(df["Scenario"].dropna().unique().tolist())
   
def save_data(df, file_path):
    try:
        df.to_csv(file_path, index=False)
        print(f"DataFrame saved to {file_path}")
    except Exception as e:
        print(f"Error saving DataFrame to {file_path}: {e}")
from utils.database_utils import engine
def load_data(file_path):
    # try:
    #     df = pd.read_csv(file_path)
    #     print(f"DataFrame loaded from {file_path}")
    #     return df
    # except Exception as e:
    #     print(f"Error loading {file_path}: {e}")
    #     return pd.DataFrame()
    try:
        query = "SELECT * FROM observations"
        df = pd.read_sql(query, engine)
        print("DataFrame loaded from Postgres")
        return df
    except Exception as e:
        print(f"Error loading data from Postgres: {e}")
        return pd.DataFrame()
    

# DATA_CSV_PATH = "data_new/all_data_melted.csv"

# if os.path.exists(DATA_CSV_PATH):
#     print("Loading prebuilt melted CSV...")
#     all_data_melted = pd.read_csv(DATA_CSV_PATH)

# else:
#     print("Melted CSV not found. Reading all CSV files and building DataFrame...")
#     all_data_df = load_and_concat_data('data')    # Save for future runs
#     all_data_melted, scenarios = melt_dataframe(all_data_df)
#     save_data(all_data_melted, "data_new/all_data_melted.csv")

  
scenarios = get_scenarios()
