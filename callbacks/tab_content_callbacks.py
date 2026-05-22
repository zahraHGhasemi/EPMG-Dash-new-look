from urllib.parse import parse_qs, urlparse, urlencode
from dash import Input, Output, State
from auth.models import db, Study
from utils.dashboard_settings import get_dashboard_settings


def _year_marks(start_year, end_year):
    """Build 5-year slider marks, always including the range endpoints."""
    marks = {str(year): str(year) for year in range(start_year, end_year + 1, 5)}
    marks[str(start_year)] = str(start_year)
    marks[str(end_year)] = str(end_year)
    return marks


def register_tab_content_callbacks(app):
    """Register callbacks for tab content visibility and URL synchronization."""
    @app.callback(
        Output("year-slider", "min"),
        Output("year-slider", "max"),
        Output("year-slider", "value"),
        Output("year-slider", "marks"),
        Output("year-sankey-slider", "min"),
        Output("year-sankey-slider", "max"),
        Output("year-sankey-slider", "value"),
        Output("year-sankey-slider", "marks"),
        Output("start-year-dropdown", "options"),
        Output("start-year-dropdown", "value"),
        Output("end-year-dropdown", "options"),
        Output("end-year-dropdown", "value"),
        Input("url", "pathname"),
    )
    def update_year_controls(_):
        """Refresh year controls from dashboard settings when the Dash page loads."""
        settings = get_dashboard_settings()
        start_year = settings["start_year"]
        end_year = settings["end_year"]
        default_start_year = settings["default_start_year"]
        default_end_year = settings["default_end_year"]
        marks = _year_marks(start_year, end_year)
        year_range = [default_start_year, default_end_year]
        options = [
            {"label": str(year), "value": year}
            for year in range(start_year, end_year + 1)
        ]

        return (
            start_year,
            end_year,
            year_range,
            marks,
            start_year,
            end_year,
            year_range,
            marks,
            options,
            default_start_year,
            options,
            default_end_year,
        )

    @app.callback(
        Output("active-study-title", "children"),
        Input("url", "search"),
    )
    def update_active_study_title(search):
        """Update the dashboard header with the active study name from the URL."""
        query = parse_qs((search or "").lstrip("?"))
        study_id = query.get("study_id", [None])[0]
        if not study_id:
            return ""

        try:
            study = db.session.get(Study, int(study_id))
        except (TypeError, ValueError):
            return ""

        return study.name if study else ""

    @app.callback(
        Output("tabs", "value"),
        Input("url", "href"),
    )
    def set_tab_from_url(href):
        """Set the active tab based on the URL query parameters."""
        default_tab = get_dashboard_settings()["default_tab"]
        if not href:
            return default_tab

        qs = parse_qs(urlparse(href).query)
        tab_from_url = qs.get("tab", [None])[0]
        if tab_from_url:
            return tab_from_url

        # If chart filters are present in a shared URL, open the Charts tab directly.
        if any(key in qs for key in ("scenario_id", "sector", "subsector")):
            return "charts"

        return default_tab
    
    @app.callback(
        Output("url", "search"),
        Input("tabs", "value"),
        State("url", "href"),
        prevent_initial_call=True
    )
    def update_url_on_tab_click(tab_value, href):
        """Update the URL query parameters when a tab is clicked, preserving existing parameters."""
        # Keep existing query params and only update tab/study_id defaults.
        if not href:
            return "?" + urlencode({"study_id": "1", "tab": tab_value})

        parsed = urlparse(href)
        qs = parse_qs(parsed.query)

        if "study_id" not in qs or not qs["study_id"] or not qs["study_id"][0]:
            qs["study_id"] = ["1"]
        qs["tab"] = [tab_value]
        if tab_value != "charts":
            qs.pop("scenario_id", None)
            qs.pop("sector", None)
            qs.pop("subsector", None)

        return "?" + urlencode(qs, doseq=True)
    
    @app.callback(
        Output("tab-about-pane", "style"),
        Output("tab-overview-pane", "style"),
        Output("tab-charts-pane", "style"),
        Output("tab-sankey-pane", "style"),
        Input("tabs", "value"),
    )
    def toggle_tab_panes(tab):
        """Toggle the visibility of tab panes based on the active tab."""
        hidden = {"display": "none"}
        visible = {"display": "block"}
        return (
            visible if tab == "about" else hidden,
            visible if tab == "overview" else hidden,
            visible if tab == "charts" else hidden,
            visible if tab == "sankey" else hidden,
        )
