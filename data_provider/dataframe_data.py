import pandas as pd
import os
from flask import session, current_app, has_request_context
from config.constants import CATEGORY_DICT


class DataFrameProvider:
    def _load_df(self):
        if not has_request_context():
            return pd.DataFrame()

        meta = session.get("user_scenario")
        if not meta:
            return pd.DataFrame()

        path = os.path.join(
            current_app.instance_path,
            "user_uploads",
            f"{meta['id']}.parquet"
        )

        if not os.path.exists(path):
            return pd.DataFrame()

        return pd.read_parquet(path, engine="pyarrow")

    def get_scenarios(self):
        df = self._load_df()
        return sorted(df["Scenario"].dropna().unique().tolist()) if not df.empty else []

    def get_categories(self):
        df = self._load_df()
        return sorted(df["cat"].dropna().unique().tolist()) if not df.empty else []

    def get_subcategories(self, category_label):
        df = self._load_df()
        df = df[df["cat"] == category_label.lower()]
        return df["tableTitle"].dropna().unique().tolist()

    def get_table_id(self, table_title, category_label):
        df = self._load_df()
        df = df[
            (df["tableTitle"] == table_title) &
            (df["cat"] == category_label.lower())
        ]
        return df["tableName"].iloc[0] if not df.empty else None
    def get_labels(self, table_id, scenario, year_range):
        df = self._load_df()
        df = df[
            (df["tableName"] == table_id) &
            (df["Scenario"] == scenario) &
            (df["Year"] >= year_range[0]) &
            (df["Year"] <= year_range[1])
        ]
        return df["label"].dropna().unique().tolist()
    def get_filtered_df(self, table_id, scenario, year_range):
        df = self._load_df()
        return df[
            (df["tableName"] == table_id) &
            (df["Scenario"] == scenario) &
            (df["Year"] >= year_range[0]) &
            (df["Year"] <= year_range[1])
        ].sort_values(["seriesName", "Year"])
