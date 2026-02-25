from urllib.parse import parse_qs, urlparse, urlencode
from dash import Input, Output, State
from components.overview import overview_layout
from components.all_charts import all_charts_layout
from components.compare import compare_charts_layout
from components.sankey import sankey_layout
from components.about import about_layout
from utils.dashboard_settings import get_dashboard_settings


def register_tab_content_callbacks(app):

    @app.callback(
        Output("tabs", "value"),
        Input("url", "href"),
    )
    def set_tab_from_url(href):
        default_tab = get_dashboard_settings()["default_tab"]
        if not href:
            return default_tab

        qs = parse_qs(urlparse(href).query)
        return qs.get("tab", [default_tab])[0]
    
    @app.callback(
        Output("url", "search"),
        Input("tabs", "value"),
        State("url", "href"),
        prevent_initial_call=True
    )
    def update_url_on_tab_click(tab_value, href):
        # Keep existing query params and only update tab/study_id defaults.
        if not href:
            return "?" + urlencode({"study_id": "1", "tab": tab_value})

        parsed = urlparse(href)
        qs = parse_qs(parsed.query)

        if "study_id" not in qs or not qs["study_id"] or not qs["study_id"][0]:
            qs["study_id"] = ["1"]
        qs["tab"] = [tab_value]

        return "?" + urlencode(qs, doseq=True)
    
    @app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value'),
        
    )
    def render_tab(tab):
       
        if tab == 'overview':
            return overview_layout()
        elif tab == 'charts':
            return compare_charts_layout()
        elif tab == 'about':
            return about_layout()
        elif tab == 'sankey':
            return sankey_layout()
