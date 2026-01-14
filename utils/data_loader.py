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
    

import pandas as pd
import io
import os

def load_and_concat_uploaded_files(files):
    """
    files: list of file-like objects (Flask FileStorage or Dash decoded bytes)

    Returns:
        pd.DataFrame
    """
    df_list = []

    for file in files:
        try:
            # --- Case 1: Flask FileStorage ---
            if hasattr(file, "filename"):
                filename = file.filename
                df = pd.read_csv(file)

            # --- Case 2: Dash dcc.Upload (bytes) ---
            else:
                filename, content = file
                content_decoded = io.StringIO(content)
                df = pd.read_csv(content_decoded)

            # --- Extract scenario name ---
            scenario_name = (
                os.path.basename(filename)
                .replace("mitigation_cb2024-", "")
                .replace(".csv", "")
            )

            df["Scenario"] = scenario_name
            df_list.append(df)

        except Exception as e:
            print(f"Error loading {filename}: {e}")

    if not df_list:
        return pd.DataFrame()

    return pd.concat(df_list, ignore_index=True)

def iter_uploaded_files_in_chunks(files, chunksize=500):
    for file in files:

        # --- Flask FileStorage ---
        if hasattr(file, "filename"):
            filename = file.filename
            reader = pd.read_csv(file, chunksize=chunksize)

        # --- Dash upload ---
        else:
            filename, content = file
            content_decoded = io.StringIO(content)
            reader = pd.read_csv(content_decoded, chunksize=chunksize)

        scenario_name = (
            os.path.basename(filename)
            .replace("mitigation_cb2024-", "")
            .replace(".csv", "")
        )

        for chunk in reader:
            chunk["Scenario"] = scenario_name
            yield chunk