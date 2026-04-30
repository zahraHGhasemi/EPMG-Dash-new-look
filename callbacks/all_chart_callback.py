from dash import Input, Output, State, no_update
from urllib.parse import urlencode, urlparse, parse_qs
from config.constants import CATEGORY_DICT
from data_provider.sql_data import SQLDataProvider
from utils.dashboard_settings import get_dashboard_settings
from auth.models import db, Study

session = db.session


def register_all_chart_callbacks(app, provider=SQLDataProvider(session=session)):
    """Register Dash callbacks that keep the all-charts filters and URL in sync."""
    @app.callback(
        Output("url", "href"),
        Input("url", "href"),
        prevent_initial_call=True
    )
    def ensure_study_in_url(href):
        """Add a default or latest study_id to the URL when one is missing."""
        if not href:
            return no_update

        parsed = urlparse(href)
        query = parse_qs(parsed.query)

        if "study_id" in query:
            return no_update

        settings = get_dashboard_settings()
        selected_study = None
        if settings.get("default_study_id"):
            selected_study = db.session.get(Study, int(settings["default_study_id"]))

        if not selected_study:
            selected_study = provider.get_latest_recent_study()

        if not selected_study:
            return no_update

        new_query = urlencode({"study_id": selected_study.id})
        return f"{parsed.path}?{new_query}"

    @app.callback(
        Output('scenario-chart-dropdown', 'options'),
        Output('scenario-chart-dropdown', 'value'),
        Input("url", "href"),
        State("scenario-chart-dropdown", "value")
    )
    def update_scenario_dropdown(href, current_value):
        """Populate scenario options for the URL study and preserve the best valid selection."""
        if not href:
            return [], None

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return [], None

        try:
            scenarios = provider.get_scenarios_for_study(int(study_id))
        except (TypeError, ValueError):
            return [], None
        options = [{"label": s.name, "value": s.name} for s in scenarios]

        selected_from_url = query.get("scenario", [None])[0]
        configured = get_dashboard_settings().get("default_scenario")
        option_values = {opt["value"] for opt in options}
        if current_value in option_values:
            value = current_value
        elif selected_from_url in option_values:
            value = selected_from_url
        elif configured in option_values:
            value = configured
        else:
            value = options[0]["value"] if options else None

        return options, value

    @app.callback(
        Output('category-dropdown', 'options'),
        Output('category-dropdown', 'value'),
        Input("scenario-chart-dropdown", "value"),
        Input("url", "href"),
        State("category-dropdown", "value")
    )
    def update_category_options(selected_scenario, href, current_value):
        """Populate sector options for the selected scenario and choose the active sector."""
        categories = provider.get_categories(selected_scenario)

        selected_from_url = None
        if href:
            query = parse_qs(urlparse(href).query)
            selected_from_url = query.get("sector", [None])[0]

        configured = get_dashboard_settings().get("default_sector")
        if current_value in categories:
            value = current_value
        elif selected_from_url in categories:
            value = selected_from_url
        elif configured in categories:
            value = configured
        elif 'SYS' in categories:
            value = 'SYS'
        else:
            value = categories[0] if categories else None

        return [{"label": CATEGORY_DICT.get(cat, cat), "value": cat} for cat in categories], value

    @app.callback(
        Output('subcategory-dropdown', 'options'),
        Output('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        State("url", "href"),
        State("subcategory-dropdown", "value")
    )
    def update_subcategory_options(category, selected_scenario, href, current_value):
        """Populate subsector options for the active sector and scenario."""
        subcategories = provider.get_subcategories(category, selected_scenario)
        legacy_default_labels = {
            "Domestic CO2 Emissions by Sector",
            "Domestic CO₂ Emissions by Sector",
        }

        selected_from_url = None
        if href:
            query = parse_qs(urlparse(href).query)
            selected_from_url = query.get("subsector", [None])[0]

        configured = get_dashboard_settings().get("default_subsector")
        if current_value in subcategories:
            value = current_value
        elif selected_from_url in subcategories:
            value = selected_from_url
        elif configured in subcategories:
            value = configured
        elif category == 'SYS' and any(label in subcategories for label in legacy_default_labels):
            value = next(label for label in legacy_default_labels if label in subcategories)
        else:
            value = subcategories[0] if subcategories else None

        return [{"label": sub, "value": sub} for sub in subcategories], value

    @app.callback(
        Output('unit-dropdown', 'options'),
        Output('unit-dropdown', 'value'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value'),
        State('unit-dropdown', 'value')
    )
    def update_unit(table_name, category, scenario, year_range, current_value):
        """Choose valid display-unit options for the selected chart table."""
        table_id = provider.get_table_id(table_name, category)
        df_unit = provider.get_labels(table_id)

        if not df_unit:
            return [], None

        label = df_unit[0]
        if label == "PJ":
            options = ['PJ', 'TWh', 'ktoe']
        elif label == "kt":
            options = ['kt', 'Mt']
        else:
            options = [label]

        if current_value in options:
            return options, current_value
        return options, options[0]

    @app.callback(
        Output("url", "search", allow_duplicate=True),
        Input("scenario-chart-dropdown", "value"),
        Input("category-dropdown", "value"),
        Input("subcategory-dropdown", "value"),
        Input("tabs", "value"),
        State("url", "href"),
        prevent_initial_call=True,
    )
    def sync_chart_filters_to_url(scenario, sector, subsector, tab, href):
        """Write chart filter selections into the URL query string while on the charts tab."""
        if tab != "charts" or not href:
            return no_update

        parsed = urlparse(href)
        query = parse_qs(parsed.query)
        changed = False
        if query.get("tab", [None])[0] != "charts":
            query["tab"] = ["charts"]
            changed = True

        if scenario and query.get("scenario", [None])[0] != scenario:
            query["scenario"] = [scenario]
            changed = True
        if sector and query.get("sector", [None])[0] != sector:
            query["sector"] = [sector]
            changed = True
        if subsector and query.get("subsector", [None])[0] != subsector:
            query["subsector"] = [subsector]
            changed = True

        if not changed:
            return no_update

        return "?" + urlencode(query, doseq=True)
