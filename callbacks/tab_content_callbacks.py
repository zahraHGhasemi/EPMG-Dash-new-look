from dash import Input, Output
from components.overview import overview_layout
from components.all_charts import all_charts_layout
from components.compare import compare_charts_layout
from components.sankey import sankey_layout
from components.about import about_layout
def register_tab_content_callbacks(app):
    @app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value'),
        
    )
    def render_tab(tab):
       
        if tab == 'overview':
            return overview_layout
        elif tab == 'compare-scenarios':
            return compare_charts_layout()
        elif tab == 'about':
            return about_layout()
        elif tab == 'sankey':
            return sankey_layout()
