import os
import base64
from dash import Input, Output, State, ctx, no_update
from utils.data_loader import load_and_concat_data
from utils.dataframe_melter import update_data_melted

UPLOAD_NEW_FILE = "data_all"
VALID_USERS = {"admin": "1234"}

UPLOAD_FOLDER = "data"  # your data folder
def process_new_scenario(data_folder, new_file_path):
    """
    When a new scenario file is uploaded, save it and update all_data_melted.
    
    Parameters:
        data_folder (str): Path to the folder containing all scenario CSV files
        new_file_path (str): Path to the new uploaded CSV file
    
    Returns:
        tuple: (updated_all_data_melted, updated_scenarios)
    """
    # 1️⃣ Ensure the file is saved in the data folder
    filename = os.path.basename(new_file_path)
    target_path = os.path.join(data_folder, filename)
    if new_file_path != target_path:
        os.replace(new_file_path, target_path)  # move uploaded file into the main folder
    
    # 2️⃣ Reload all CSV files (including the new one)
    all_data_df = load_and_concat_data(data_folder)
    
    # 3️⃣ Melt and process all data using your existing function
    all_data_melted, scenarios = update_data_melted(all_data_df)
    
    # 4️⃣ Optionally save the melted data to a file
    all_data_melted.to_csv(os.path.join(UPLOAD_NEW_FILE, "all_data_melted.csv"), index=False)
    
    print(f"✅ Added and processed new scenario: {filename}")
    print(f"📊 Total scenarios now: {len(scenarios)}")
    
    return all_data_melted, scenarios


# Simple credentials (for demo)


def register_upload_callback(app):

    @app.callback(
        Output("upload-modal", "style"),
        [Input("open-upload-modal", "n_clicks"),
         Input("close-upload-modal", "n_clicks")],
        prevent_initial_call=True
    )
    def toggle_modal(open_click, close_click):
        trigger = ctx.triggered_id
        base_style = {
            "position": "fixed",
            "top": "20%",
            "left": "35%",
            "width": "30%",
            "background": "white",
            "border": "1px solid #ccc",
            "padding": "20px",
            "zIndex": 1000
        }
        if trigger == "open-upload-modal":
            return {"display": "block", "position": "fixed", "top": "20%", "left": "35%", "width": "30%",
                    "background": "white", "border": "1px solid #ccc", "padding": "20px", "zIndex": 1000}
        else:
            return {"display": "none"}

    @app.callback(
        Output("login-status", "children"),
        Output("upload-data", "disabled"),
        Input("login-btn", "n_clicks"),
        State("username", "value"),
        State("password", "value"),
        prevent_initial_call=True
    )
    def login(n, username, password):
        if username in VALID_USERS and VALID_USERS[username] == password:
            return "✅ Login successful. You can now upload a file.", False
        return "❌ Invalid username or password.", True

    @app.callback(
        Output("scenario-dropdown", "options"),
        Output("scenario-dropdown", "value"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        State("scenario-dropdown", "options"),
        prevent_initial_call=True
    )
    def save_uploaded_file(contents, filename, current_options):
        if contents is None:
            return no_update

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as f:
            f.write(decoded)
        
        all_data_melted, scenarios = process_new_scenario(UPLOAD_FOLDER, file_path)

        new_options = [{"label": s, "value": s} for s in scenarios]
        new_value = scenarios[-1] if scenarios else None
        return new_options, new_value
