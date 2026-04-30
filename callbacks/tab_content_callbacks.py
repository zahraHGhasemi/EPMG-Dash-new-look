from urllib.parse import parse_qs, urlparse, urlencode
from dash import Input, Output, State
from utils.dashboard_settings import get_dashboard_settings


def register_tab_content_callbacks(app):
    """Register callbacks for tab content visibility and URL synchronization."""
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
        if any(key in qs for key in ("scenario", "sector", "subsector")):
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
            qs.pop("scenario", None)
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
