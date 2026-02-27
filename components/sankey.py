import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dcc
from utils.dashboard_settings import get_dashboard_settings


def sankey_layout ():
    settings = get_dashboard_settings()
    start_year = settings["start_year"]
    end_year = settings["end_year"]
    default_start_year = settings["default_start_year"]
    default_end_year = settings["default_end_year"]
    sankey_mode = settings["sankey_mode"]

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Year Range"),
                dcc.RangeSlider(
                    id='year-sankey-slider',
                    min=start_year, #all_data_melted['Year'].min(),
                    max=end_year, #all_data_melted['Year'].max()-1,
                    value=[default_start_year, default_end_year],
                    marks={str(year): str(year) for year in range(start_year, end_year + 1, 5)}, #range(all_data_melted['Year'].min(), all_data_melted['Year'].max(), 1)},
                    step=1,
                    persistence=True,
                    persistence_type='session'
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Scenario"),
                dcc.Dropdown(
                    id='scenario-sankey-dropdown',
                    persistence=True,
                    persistence_type='session',
                    # options= [{'label': s, 'value': s} for s in scenarios],
                    # value= scenarios[0] if len(scenarios) > 0 else None,
                )
            ], width=6),
            dbc.Col([
                html.Label("Title"),
                dcc.Dropdown(
                    id="sankey_title_dropdown",
                    options=[
                        {'label': 'Primary Energy to Demand detailed', 'value': 0},
                        {'label': 'Primary Energy to Final Energy', 'value': 1}
                    ],
                    value=sankey_mode,
                    persistence=True,
                    persistence_type='session'
                )
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Spinner(
                    dcc.Graph(
                        id = "sankey-diagram",
                        style={'height': '600px'},
                        config={'responsive': True}
                    ),
                    color="primary",      # spinner color
                    size="lg",            # spinner size
                    type="border"         # or "grow"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Spinner(
                    dcc.Graph(
                        id = "sankey-end-diagram",
                        style={'height': '600px'},
                        config={'responsive': True}
                    ),
                    color="primary",      # spinner color
                    size="lg",            # spinner size
                    type="border"         # or "grow"
                )
            ])
        ])

    ])
    
