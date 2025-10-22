import glob
import os
import pandas as pd
def load_and_concat_data(directory_path):
    all_files = glob.glob(os.path.join(directory_path, "*.csv"))
    df_list = []
    for file_path in all_files:
        try:
            df = pd.read_csv(file_path)
            # Extract scenario name from filename
            file_name = os.path.basename(file_path)
            scenario_name = file_name.replace("mitigation_cb2024-", "").replace(".csv", "")
            df['Scenario'] = scenario_name
            df_list.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if df_list:
        concatenated_df = pd.concat(df_list, ignore_index=True)
        
        return concatenated_df
    else:
        return pd.DataFrame()
    
