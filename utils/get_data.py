
# from utils.dataframe_melter import all_data_melted
from utils.config_loader import chartsTitle
from utils.database_utils import read_sql
# df = all_data_melted
category_dic = { 'Transport': 'TRA',
                'Residential': 'RSD',
                'Services': 'SRV',
                'Industry': 'IND',
                'Power': 'PWR',
                'Supply': 'SUP',
                'Agriculture': 'AGR',
                'System': 'SYS'
                }
def get_categories(df_1):
    query = 'SELECT DISTINCT "cat" FROM observations'
    df = read_sql(query)
    return df["cat"].dropna().tolist()


def get_subcategories(category):
    category_id = category_dic.get(category, "").lower()
    query = """
        SELECT DISTINCT "tableTitle"
        FROM observations
        WHERE "cat" = :cat
    """
    df = read_sql(query, params={"cat": category_id})
    return df["tableTitle"].dropna().tolist()

def get_table_id(table_name, category):
    category_id = category_dic.get(category, "").lower()
    query = """
        SELECT "tableName"
        FROM observations
        WHERE "tableTitle" = :tableTitle AND "cat" = :cat
        LIMIT 1
    """
    df = read_sql(query, params={"tableTitle": table_name, "cat": category_id})
    return df["tableName"].iloc[0] if not df.empty else None
def get_filtered_df(table_id, scenario, year_range):
    """Filter observations by tableName, Scenario, and Year range."""
    query = """
        SELECT *
        FROM observations
        WHERE "tableName" = :tableName
          AND "Scenario" = :scenario
          AND "Year" BETWEEN :year_start AND :year_end
    """
    df = read_sql(query, params={
        "tableName": table_id,
        "scenario": scenario,
        "year_start": year_range[0],
        "year_end": year_range[1]
    })
    return df

# def get_categories(df):
#     return df['cat'].unique().tolist()

# def get_subcategories(category):
    
#     category_id = category_dic[category].lower()
    
#     df_filtered = df[df['cat']== category_id]
#     print(df_filtered['tableTitle'].unique().tolist())
#     return df_filtered['tableTitle'].unique().tolist()

# def get_table_id(table_name,category):
#     return df[(df['tableTitle'] == table_name) & (df['cat']== category_dic[category].lower())]['tableName'].iloc[0]
   
# def get_filtered_df(table_id, scenario, year_range):
#     filtered_data = all_data_melted[(all_data_melted['tableName'] == table_id)&
#                                     (all_data_melted['Scenario']== scenario)&
#                                     (all_data_melted['Year'] >= year_range[0])&
#                                     (all_data_melted['Year'] <= year_range[1])]
#     return filtered_data
def get_subcategory_name(subcategory):
    print(subcategory, 'subcategory input')
    if subcategory in chartsTitle:
        print(chartsTitle[subcategory], 'subcategory name')
        return chartsTitle[subcategory]
    else:
        return subcategory