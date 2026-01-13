



import dash
from dash import dcc, html

import plotly.express as px
import dash_bootstrap_components as dbc
from callbacks.overview_callback import register_overview_callbacks

from callbacks.tab_content_callbacks import register_tab_content_callbacks

from callbacks.all_chart_callback import register_all_chart_callbacks
from callbacks.compare_callback import register_compare_chart_callbacks
from callbacks.sankey_callback import register_sankey_callback

from data_provider.sql_data import SQLDataProvider

# from components.navbar import navbar

def init_dash(server):
    app = dash.Dash(
        __name__,
        server=server,  # ✅ IMPORTANT: attach Dash to existing Flask server
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        url_base_pathname="/dash/"
    )
    # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
    #     suppress_callback_exceptions=True)
    # server = app.server
    # all_data_melted = get_data_melted()
    app.title = "Energy Scenarios Dashboard"
    main_layout =  html.Div([
        html.Div([
            html.Img(
                src="assets/EPMG LOGO.png",
                style={
                    "height": "60px",
                    "margin-right": "15px"
                }
            ),
            html.H1(
                "Energy Policy & Modeling Group Dashboard",
                style={
                    "margin": "0",
                    "font-size": "36px"
                }
            )
        ],
        style={
            "display": "flex",
            "alignItems": "center",     # vertical alignment
            "justifyContent": "center", # horizontal centering
            "padding": "20px"
        }), 
        
        dbc.Row([       
            dbc.Col([
                dcc.Tabs(id ='tabs', value = 'about', children =[
                    dcc.Tab(label = 'About', value = 'about'),
                    dcc.Tab(label='Overview', value='overview'),
                    # dcc.Tab(label='Chart Detail', value='all-charts'),
                    dcc.Tab(label='Charts', value='compare-scenarios'),
                    dcc.Tab(label= "Sankey Diagram", value = 'sankey')
                ]),
        html.Div(id='tab-content', children='Loading...'),
            ], width=12)
        ])
        
    ])

    app.layout = html.Div([
            main_layout
        ])
    provider = SQLDataProvider(table_name="observations")
    register_tab_content_callbacks(app)

    register_overview_callbacks(app) 

    register_all_chart_callbacks(app,provider=provider)
    register_compare_chart_callbacks(app,provider=provider)
    register_sankey_callback(app)

    return app

    # import os
    # if __name__ == '__main__':
    #     port = int(os.environ.get("PORT", 8050))
    #     app.run(host="0.0.0.0", port=port, debug=True)
    #     # app.run(debug=True)
