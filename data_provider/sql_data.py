# from utils.database_utils import read_sql
# from config.constants import CATEGORY_DICT


# class SQLDataProvider:
#     def __init__(self, table_name="observations"):
#         self.table = table_name

#     def get_scenarios(self):
#         query = f'''
#             SELECT DISTINCT "Scenario"
#             FROM {self.table}
#             ORDER BY "Scenario"
#         '''
#         df = read_sql(query)
#         return df["Scenario"].dropna().tolist()

#     def get_categories(self):
#         query = f'''
#             SELECT DISTINCT "cat"
#             FROM {self.table}
#         '''
#         df = read_sql(query)
#         return df["cat"].dropna().tolist()

#     def get_subcategories(self, category_label):
#         if not category_label:
#             return []

#         query = f'''
#             SELECT DISTINCT "tableTitle"
#             FROM {self.table}
#             WHERE "cat" = :cat
#         '''
#         df = read_sql(query, params={"cat": category_label.lower()})
#         return df["tableTitle"].dropna().tolist()

#     def get_table_id(self, table_title, category_label):
#         if not category_label:
#             return None

#         query = f'''
#             SELECT "tableName"
#             FROM {self.table}
#             WHERE "tableTitle" = :title
#               AND "cat" = :cat
#             LIMIT 1
#         '''
#         df = read_sql(query, params={
#             "title": table_title,
#             "cat": category_label.lower()
#         })
#         return df.iloc[0, 0] if not df.empty else None
#     def get_labels(self, table_id, scenario, year_range):
#         query = f'''
#             SELECT *
#             FROM {self.table}
#             WHERE "tableName" = :table
#               AND "Scenario" = :scenario
#               AND "Year" BETWEEN :y0 AND :y1
#             ORDER BY "seriesName", "Year"
#         '''
#         df = read_sql(query, params={
#             "table": table_id,
#             "scenario": scenario,
#             "y0": year_range[0],
#             "y1": year_range[1],
#         })
#         return df["label"].unique().tolist()
#     def get_filtered_df(self, table_id, scenario, year_range):
#         query = f'''
#             SELECT *
#             FROM {self.table}
#             WHERE "tableName" = :table
#               AND "Scenario" = :scenario
#               AND "Year" BETWEEN :y0 AND :y1
#             ORDER BY "seriesName", "Year"
#         '''
#         return read_sql(query, params={
#             "table": table_id,
#             "scenario": scenario,
#             "y0": year_range[0],
#             "y1": year_range[1],
#         })

from auth.models import Scenario, StudyScenario, Table, Series, Year, Value, Study, db
from sqlalchemy import select
import pandas as pd

class SQLDataProvider:
    def __init__(self, session):
        self.session = session

    def get_scenarios(self):
        rows = self.session.execute(
            select(Scenario.name).order_by(Scenario.name)
        ).all()
        return [name for (name,) in rows]
    def get_categories(self):
        rows = self.session.execute(
            select(Table.category).distinct().order_by(Table.category)
        ).all()
        return [cat for (cat,) in rows]
    def get_subcategories(self, category_label):
        if not category_label:
            return []

        rows = self.session.execute(
            select(Table.title)
            .where(Table.category == category_label)
            .order_by(Table.title)
        ).all()
        return [title for (title,) in rows]
    def get_table_id(self, table_title, category_label):
        row = self.session.execute(
            select(Table.id)
            .where(Table.title == table_title)
            .where(Table.category == category_label)
        ).scalar_one_or_none()
        return row  # returns table_id or None
    def get_labels(self, table_id):
        row = self.session.execute(
            select(Table.label)
            .where(Table.id == table_id)
        ).all()

        # Collect series titles
        return [label for (label,) in row]
    
    def get_filtered_df(self, table_id, scenario_name, year_range):
        scenario_id = self.session.execute(
            select(Scenario.id)
            .where(Scenario.name == scenario_name)
        ).scalar_one()

        # Join Value → Series → Table → Year
        query = (
            select(Series.title.label("seriesTitle"),
                   Series.name.label("seriesName"),
                   Value.year.label("Year"),
                   Value.value.label("Value"))
            .join(Value, Value.series_id == Series.id)
            .where(Series.table_id == table_id)
            .where(Value.scenario_id == scenario_id)
            .where(Value.year.between(year_range[0], year_range[1]))
            .order_by(Series.name, Value.year)
        )

        rows = self.session.execute(query).all()
        df = pd.DataFrame(rows, columns=["seriesTitle", "seriesName", "Year", "Value"])
        return df
    
    def get_series_titles(self, table_id):
        rows = self.session.execute(
            select(Series.title)
            .where(Series.table_id == table_id)
            .order_by(Series.title)
        ).all()
        return [title for (title,) in rows]
    def get_table_id_by_name(self, table_name):
        row = self.session.execute(
            select(Table.id)
            .where(Table.name == table_name)
            .where(Table.category == table_name[:3])
        ).scalar_one_or_none()
        return row  # returns table_id or None
    
    def get_studies_by_status(self, status):
        return (
            self.session.query(Study)
            .filter_by(status=status)
            .order_by(Study.name)
            .all()
        )

    def get_scenarios_for_study(self, study_id):
        return (
            self.session.query(Scenario)
            .join(StudyScenario)
            .filter(StudyScenario.study_id == study_id)
            .order_by(Scenario.name)
            .all()
        )
    def get_latest_recent_study(self):
        return (
            Study.query
            .filter(Study.status == "recent")
            .order_by(Study.id.desc())
            .first()
        )
    def get_recent_studies(self):
        return self.get_studies_by_status("recent")
    def get_archive_studies(self):
        return self.get_studies_by_status("archive")