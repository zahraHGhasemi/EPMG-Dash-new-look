from utils.database_utils import read_sql
from config.constants import CATEGORY_DICT


class SQLDataProvider:
    def __init__(self, table_name="observations"):
        self.table = table_name

    def get_scenarios(self):
        query = f'''
            SELECT DISTINCT "Scenario"
            FROM {self.table}
            ORDER BY "Scenario"
        '''
        df = read_sql(query)
        return df["Scenario"].dropna().tolist()

    def get_categories(self):
        query = f'''
            SELECT DISTINCT "cat"
            FROM {self.table}
        '''
        df = read_sql(query)
        return df["cat"].dropna().tolist()

    def get_subcategories(self, category_label):
        if not category_label:
            return []

        query = f'''
            SELECT DISTINCT "tableTitle"
            FROM {self.table}
            WHERE "cat" = :cat
        '''
        df = read_sql(query, params={"cat": category_label.lower()})
        return df["tableTitle"].dropna().tolist()

    def get_table_id(self, table_title, category_label):
        if not category_label:
            return None

        query = f'''
            SELECT "tableName"
            FROM {self.table}
            WHERE "tableTitle" = :title
              AND "cat" = :cat
            LIMIT 1
        '''
        df = read_sql(query, params={
            "title": table_title,
            "cat": category_label.lower()
        })
        return df.iloc[0, 0] if not df.empty else None
    def get_labels(self, table_id, scenario, year_range):
        query = f'''
            SELECT *
            FROM {self.table}
            WHERE "tableName" = :table
              AND "Scenario" = :scenario
              AND "Year" BETWEEN :y0 AND :y1
            ORDER BY "seriesName", "Year"
        '''
        df = read_sql(query, params={
            "table": table_id,
            "scenario": scenario,
            "y0": year_range[0],
            "y1": year_range[1],
        })
        return df["label"].unique().tolist()
    def get_filtered_df(self, table_id, scenario, year_range):
        query = f'''
            SELECT *
            FROM {self.table}
            WHERE "tableName" = :table
              AND "Scenario" = :scenario
              AND "Year" BETWEEN :y0 AND :y1
            ORDER BY "seriesName", "Year"
        '''
        return read_sql(query, params={
            "table": table_id,
            "scenario": scenario,
            "y0": year_range[0],
            "y1": year_range[1],
        })
