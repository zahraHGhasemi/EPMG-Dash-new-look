
from utils.dataframe_melter import all_data_melted
from utils.config_loader import chartsTitle
df = all_data_melted
category_dic = { 'Transport': 'TRA',
                'Residential': 'RSD',
                'Services': 'SRV',
                'Industry': 'IND',
                'Power': 'PWR',
                'Supply': 'SUP',
                'Agriculture': 'AGR',
                'System': 'SYS'
                }

def get_categories(df):
    return df['cat'].unique().tolist()

def get_subcategories(category):
    
    category_id = category_dic[category].lower()
    
    df_filtered = df[df['cat']== category_id]
    print(df_filtered['tableTitle'].unique().tolist())
    return df_filtered['tableTitle'].unique().tolist()

def get_table_id(table_name,category):
    return df[(df['tableTitle'] == table_name) & (df['cat']== category_dic[category].lower())]['tableName'].iloc[0]
   
def get_filtered_df(table_id, scenario, year_range):
    filtered_data = all_data_melted[(all_data_melted['tableName'] == table_id)&
                                    (all_data_melted['Scenario']== scenario)&
                                    (all_data_melted['Year'] >= year_range[0])&
                                    (all_data_melted['Year'] <= year_range[1])]
    return filtered_data
def get_subcategory_name(subcategory):
    print(subcategory, 'subcategory input')
    print(chartsTitle[subcategory], 'subcategory name')
    if subcategory in chartsTitle:
        return chartsTitle[subcategory]
    else:
        return subcategory