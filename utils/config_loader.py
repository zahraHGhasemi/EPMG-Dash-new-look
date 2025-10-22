import pandas as pd
import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")

def load_json_as_dict(filename):
    """Load a JSON file as a Python dictionary."""
    filepath = os.path.join(CONFIG_DIR, filename)
    with open(filepath, "r") as f:
        return json.load(f)

def load_json_as_df(filename):
    """Load a JSON file as a Pandas DataFrame (for dictionary-style JSONs)."""
    filepath = os.path.join(CONFIG_DIR, filename)
    df = pd.read_json(filepath, orient="index")
    df.reset_index(inplace=True)
    if filename.find("charts")== 0:
      df.rename(columns={"index": "tableName"}, inplace=True)
    else:
      df.rename(columns={"index": "seriesName"}, inplace=True)
    
    return df    

chartsInfo = load_json_as_df("chartsInfo.json")
chartsTitle = load_json_as_df("chartsTitles.json")
seriesTitle = load_json_as_df("seriesTitles.json")

# def load_config():
#     """Load configuration from a JSON file."""
#     chartsInfo = pd.read_json("./config/chartsInfo.json", orient='index')
#     chartsTitle = pd.read_json("./config/chartsTitle.json", orient='index')
#     seriesTitle = pd.read_json("./config/seriesTitle.json", orient='index')

#     return [chartsInfo, chartsTitle, seriesTitle]