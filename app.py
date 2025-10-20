

import pandas as pd
import numpy as np

import dash
from dash import dcc, html, Input, Output

import plotly.express as px
import dash_bootstrap_components as dbc
# from utils.data_loader import load_and_concat_data
# from utils.dataframe_melter import melt_dataframe
# from components.overview import overview_layout
# from components.supply import supply_layout
# from components.power import power_layout
# from components.sector import sector_layout
# from components.search import search_layout
# from components.emissionCO2 import emissionCO2_layout   
from callbacks.overview_callback import register_overview_callbacks
# from callbacks.supply_callback import register_supply_callbacks
# from callbacks.power_callback import register_power_callbacks
# from callbacks.emissionCO2_callback import register_emissionCO2_callback
# from callbacks.sector_callback import register_sector_callbacks
# from callbacks.subsector_callbacks.subsector_overview_callback import register_subsector_overview_callback
# from callbacks.subsector_callbacks.subsector_transport_callback import register_subsector_transport_callback
# from callbacks.subsector_callbacks.subsector_residential_callback import register_subsector_residential_callback
# from callbacks.subsector_callbacks.subsector_services_callback import register_subsector_services_callback
# from callbacks.subsector_callbacks.subsector_industry_callback import register_subsector_industry_callback
# from callbacks.search_callback import register_search_callbacks
from callbacks.tab_content_callbacks import register_tab_content_callbacks
from callbacks.upload_file_callback import register_upload_callback
from utils.dataframe_melter import get_scenarios, get_data_melted
from callbacks.all_chart_callback import register_all_chart_callbacks
from callbacks.compare_callback import register_compare_chart_callbacks


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True)
server = app.server


scenarios = get_scenarios()
# all_data_melted = get_data_melted()
app.title = "Energy Scenarios Dashboard"

app.layout = html.Div([
    html.Div([
        html.Img(
            src="/assets/EPMG LOGO.png",
            style={
                "height": "60px",
                "margin-right": "15px"
            }
        ),
        html.H1(
            "Energy Policy Modeling Group Dashboard",
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
        # dbc.Col([
        #     html.Div([
        #         html.Label("Select Scenario:", className="control-label"),
        #         dbc.RadioItems(
        #             id='scenario-dropdown',
        #             options=[{'label': s, 'value': s} for s in scenarios],
        #             value=scenarios[0] if len(scenarios) > 0 else None,
        #             # placeholder="Select a scenario...",
        #             # className="dropdown"
        #         ),
        #         
        dbc.Col([
            dcc.Tabs(id ='tabs', value = 'overview', children =[
                dcc.Tab(label='Overview', value='overview'),
                dcc.Tab(label='Chart Detail', value='all-charts'),
                dcc.Tab(label='Compare Scenarios', value='compare-scenarios'),
            ]),
    html.Div(id='tab-content', children='Loading...'),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col(
        [html.Button("Upload Scenario", id="open-upload-modal", n_clicks=0, style = {'margin': '10px'} )
        ], width=2),
    ]),
    
    html.Div(
        id="upload-modal",
        style={"display": "none", "position": "fixed", "top": "20%", "left": "35%", "width": "30%",
                "background": "white", "border": "1px solid #ccc", "padding": "20px", "zIndex": 1000},
        children=[
            html.H4("Upload Scenario"),
            dcc.Input(id="username", placeholder="Username", type="text", style={"width": "100%"}),
            dcc.Input(id="password", placeholder="Password", type="password", style={"width": "100%", "marginTop": "10px"}),
            html.Button("Login", id="login-btn", n_clicks=0, style={"marginTop": "10px"}),
            html.Button("Close", id="close-upload-modal", n_clicks=0, style={"marginLeft": "10px"}),
            html.Div(id="login-status", style={"marginTop": "10px"}),
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                style={"width": "100%", "height": "60px", "lineHeight": "60px",
                       "borderWidth": "1px", "borderStyle": "dashed", "borderRadius": "5px",
                       "textAlign": "center", "marginTop": "10px"},
                multiple=False
            )
        ]
    )
])

register_tab_content_callbacks(app)
# register_overview_callbacks(app, all_data_melted)
# register_supply_callbacks(app, all_data_melted)
# register_power_callbacks(app, all_data_melted)
# register_sector_callbacks(app, all_data_melted)
# register_emissionCO2_callback(app, all_data_melted)
# register_search_callbacks(app, all_data_melted)
# register_subsector_overview_callback(app, all_data_melted)
# register_subsector_transport_callback(app, all_data_melted) 
# register_subsector_residential_callback(app,all_data_melted)
# register_subsector_services_callback(app,all_data_melted)
# register_subsector_industry_callback(app,all_data_melted)

register_overview_callbacks(app) #, all_data_melted)
# register_supply_callbacks(app)#, all_data_melted)
# register_power_callbacks(app)#, all_data_melted)
# register_sector_callbacks(app)#, all_data_melted)
# register_emissionCO2_callback(app)#, all_data_melted)
# register_search_callbacks(app)#, all_data_melted)
# register_subsector_overview_callback(app)#, all_data_melted)
# register_subsector_transport_callback(app)#, all_data_melted) 
# register_subsector_residential_callback(app)#,all_data_melted)
# register_subsector_services_callback(app)#,all_data_melted)
# register_subsector_industry_callback(app)#,all_data_melted)

register_upload_callback(app)

register_all_chart_callbacks(app)
register_compare_chart_callbacks(app)
import os
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)
    # app.run(debug=True)

