import pandas as pd
from utils.config_loader import chartsInfo, chartsTitle, seriesTitle


def get_table_id( table_name):
  filtered_df = chartsTitle[chartsTitle[0]== table_name]
  if not filtered_df.empty:
    return filtered_df['tableName'].iloc[0]
  else:
    return None # Or raise an error, depending on desired behavior
def get_series_name(table_name):
  table_name_id = get_table_id(table_name)
  df_option = seriesTitle[seriesTitle['seriesName'].isin(chartsInfo[chartsInfo['tableName'] == table_name_id]['seriesNames'].iloc[0])]
  return df_option[0]

