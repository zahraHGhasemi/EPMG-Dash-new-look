import dash
from dash import dcc, html
from dash import clientside_callback, Input, Output, State
from urllib.parse import parse_qs

from flask import render_template, request
import plotly.express as px
import dash_bootstrap_components as dbc
from callbacks.about_callback import register_about_callbacks
from callbacks.overview_callback import register_overview_callbacks

from callbacks.tab_content_callbacks import register_tab_content_callbacks

from callbacks.all_chart_callback import register_all_chart_callbacks
from callbacks.compare_callback import register_compare_chart_callbacks
from callbacks.sankey_callback import register_sankey_callback
from components.overview import overview_layout
from components.compare import compare_charts_layout
from components.about import about_layout
from components.sankey import sankey_layout

from data_provider.sql_data import SQLDataProvider

from auth.models import db, Study

session = db.session

def init_dash(server):
    """Initialize the Dash app with the given Flask server, set up the layout, and register callbacks."""
    app = dash.Dash(
        __name__,
        server=server,  
        external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
        suppress_callback_exceptions=True,
        url_base_pathname="/dash/"
    )
    
    app.title = "Energy Scenarios Dashboard"
    main_layout =  html.Div([
        dcc.Location(id = 'url', refresh = False),
        html.Div(id="url-sync-dummy", style={"display": "none"}),
        dcc.Store(id="tab-state-store", storage_type="session"),

        html.Div([
            html.Img(
                src="assets/EPMG LOGO.png",
                style={
                    "height": "60px",
                    "margin-right": "15px"
                }
            ),
            html.Div([
                html.H1(
                    "Energy Policy & Modeling Group Dashboard",
                    style={
                        "margin": "0",
                        "font-size": "36px",
                        "font-weight": "500"
                    }
                ),
                html.H2(
                    id="active-study-title",
                    style={
                        "margin": "4px 0 0",
                        "font-size": "24px",
                        "font-weight": "700"
                    }
                )
            ],
            style={
                "textAlign": "center"
            })
        ],
        style={
            "display": "flex",
            "alignItems": "center",    
            "justifyContent": "center", 
            "padding": "20px"
        }), 
        
        dbc.Row([       
            dbc.Col([
                dcc.Tabs(id ='tabs', value = 'about', children =[
                    dcc.Tab(label = 'About', value = 'about'),
                    dcc.Tab(label='Overview', value='overview'),
                    dcc.Tab(label='Charts', value='charts'),
                    dcc.Tab(label= "Sankey Diagram", value = 'sankey')
                ]),
        html.Div(
            id='tab-content',
            children=[
                html.Div(id="tab-about-pane", children=about_layout()),
                html.Div(id="tab-overview-pane", children=overview_layout(), style={"display": "none"}),
                html.Div(id="tab-charts-pane", children=compare_charts_layout(), style={"display": "none"}),
                html.Div(id="tab-sankey-pane", children=sankey_layout(), style={"display": "none"}),
            ]
        ),
            ], width=12)
        ])
        
    ])
    
    app.layout = html.Div([
            main_layout
        ])
    provider = SQLDataProvider(session=session)

    @app.callback(
        Output("active-study-title", "children"),
        Input("url", "search"),
    )
    def update_active_study_title(search):
        query = parse_qs((search or "").lstrip("?"))
        study_id = query.get("study_id", [None])[0]
        if not study_id:
            return ""

        try:
            study = db.session.get(Study, int(study_id))
        except (TypeError, ValueError):
            return ""

        return study.name if study else ""

    app.clientside_callback(
    """
    function(search, tab) {
        const params = new URLSearchParams(search || "");
        const study_id = params.get("study_id") || "1";

        params.set("study_id", study_id);
        if (tab) {
            params.set("tab", tab);
        }

        const newUrl = "/dashboard?" + params.toString();

        window.parent.postMessage(
            {type: "DASH_URL_UPDATE", url: newUrl},
            "*"
        );

        return "";
    }
    """,
    Output("url-sync-dummy", "children"),
    Input("url", "search"),
    State("tabs", "value"),
)

    register_tab_content_callbacks(app)

    register_overview_callbacks(app, provider=provider) 
    register_about_callbacks(app)
    register_all_chart_callbacks(app,provider=provider)
    register_compare_chart_callbacks(app,provider=provider)
    register_sankey_callback(app)

    return app

 
