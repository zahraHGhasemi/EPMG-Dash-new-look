from auth.models import Scenario, StudyScenario, Table, Series, Value, Study
from sqlalchemy import or_, select
import pandas as pd

class SQLDataProvider:
    """
    A data provider for fetching scenario, category, and table information from the database.
    """
    def __init__(self, session):
        self.session = session

    def get_scenarios(self):
        """Fetch all scenario names from the database."""
        rows = self.session.execute(
            select(Scenario.name).order_by(Scenario.name)
        ).all()
        return [name for (name,) in rows]
    def get_categories(self, scenario_name=None):
        """Fetch category labels, optionally filtered by scenario name."""
        query = select(Table.category).distinct()
        if scenario_name:
            query = (
                query
                .join(Series, Series.table_id == Table.id)
                .join(Value, Value.series_id == Series.id)
                .join(Scenario, Scenario.id == Value.scenario_id)
                .where(Scenario.name == scenario_name)
            )
        rows = self.session.execute(query.order_by(Table.category)).all()
        return [cat for (cat,) in rows]
    def get_subcategories(self, category_label, scenario_name=None):
        """Fetch distinct table titles for a given category label, optionally filtered by scenario name."""
        if not category_label:
            return []

        query = select(Table.title).where(Table.category == category_label)
        if scenario_name:
            query = (
                query
                .join(Series, Series.table_id == Table.id)
                .join(Value, Value.series_id == Series.id)
                .join(Scenario, Scenario.id == Value.scenario_id)
                .where(Scenario.name == scenario_name)
            )
        rows = self.session.execute(query.distinct().order_by(Table.title)).all()
        return [title for (title,) in rows]
    def get_table_id(self, table_title, category_label):
        """Fetch the table ID for a given table title and category label."""
        row = self.session.execute(
            select(Table.id)
            .where(Table.title == table_title)
            .where(Table.category == category_label)
        ).scalar_one_or_none()
        return row  # returns table_id or None
    def get_labels(self, table_id):
        """Fetch series titles for a given table ID."""
        row = self.session.execute(
            select(Table.label)
            .where(Table.id == table_id)
        ).all()

        # Collect series titles
        return [label for (label,) in row]
    
    def get_filtered_df(self, table_id, scenario_name, year_range):
        """Fetch a DataFrame of series titles, years, and values for a given table ID, scenario name, and year range."""
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
        """Fetch series titles for a given table ID."""
        rows = self.session.execute(
            select(Series.title)
            .where(Series.table_id == table_id)
            .order_by(Series.title)
        ).all()
        return [title for (title,) in rows]
    def get_series_titles_with_colors(self, table_id):
        """Fetch series titles and their associated colors for a given table ID."""
        rows = self.session.execute(
            select(Series.id, Series.title, Series.color)
            .where(Series.table_id == table_id)
            .order_by(Series.title)
        ).all()
        return [{"id": series_id, "title": title, "color": color} for series_id, title, color in rows]
    def get_series_color_map_by_title(self, table_id):
        """Fetch a mapping of series titles to their associated colors for a given table ID."""
        rows = self.session.execute(
            select(Series.title, Series.color)
            .where(Series.table_id == table_id)
            .where(Series.color.is_not(None))
        ).all()
        return {title: color for title, color in rows if title and color}
    def get_series_color_map_by_list_titles(self, list_table_ids=None):
        """Fetch a mapping of series titles to their associated colors for a list of table IDs."""
        rows = self.session.execute(
            select(Series.title, Series.color)
            .where(
                Series.color.is_not(None),
                Series.table_id.in_(list_table_ids)
            )
            .order_by(Series.table_id, Series.id)
        ).all()
        color_map = {}
        for title, color in rows:
            if title and color and title not in color_map:
                color_map[title] = color
        return color_map
    def get_table_id_by_name(self, table_name):
        """Fetch the table ID for a given table name."""
        row = self.session.execute(
            select(Table.id)
            .where(Table.name == table_name)
            .where(Table.category == table_name[:3])
        ).scalar_one_or_none()
        return row  # returns table_id or None
    
    def get_studies_by_status(self, status):
        """Fetch studies filtered by their status (e.g., 'recent', 'archive', 'ongoing')."""
        return (
            self.session.query(Study)
            .filter_by(status=status)
            .order_by(Study.name)
            .all()
        )

    def get_scenarios_for_study(self, study_id):
        """Fetch scenarios associated with a given study ID."""
        return (
            self.session.query(Scenario)
            .join(StudyScenario)
            .filter(StudyScenario.study_id == study_id)
            .order_by(Scenario.name)
            .all()
        )
    def get_latest_recent_study(self):
        """Fetch the most recent study with status 'recent'."""
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
    def get_ongoing_studies(self):
        return self.get_studies_by_status("ongoing")
    def check_table_include_name(self, scenario_name, category_prefix, name_substrings):
        """Check if tables for a given scenario and category prefix include any of the specified substrings in their names."""
        scenario_id = self.session.execute(
        select(Scenario.id).where(Scenario.name == scenario_name)
        ).scalar_one_or_none()

        if scenario_id is None:
            return []

        query = (
            select(Table.name)
            .join(Series, Series.table_id == Table.id)
            .join(Value, Value.series_id == Series.id)
            .where(Table.category.like(f"{category_prefix}%"))
            .where(Value.scenario_id == scenario_id)
        )

        if name_substrings:
            substring_conditions = [
                Table.name.ilike(f"%{substring}%")
                for substring in name_substrings
            ]
            query = query.where(or_(*substring_conditions))

        query = query.distinct()

        result = self.session.execute(query).scalars().all()
        result.remove(category_prefix + '_' + 'FEC') if category_prefix + '_FEC' in result else None
        return result
    def get_table_title_by_name(self, table_name):
        """Fetch the table title for a given table name."""
        row = self.session.execute(
            select(Table.title)
            .where(Table.name == table_name)
        ).scalar_one_or_none()
        return row  