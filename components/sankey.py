import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dcc
from utils.dataframe_melter import get_scenarios

scenarios = get_scenarios()
def sankey_layout ():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Year"),
                dcc.Dropdown(
                    id='year-sankey-dropdown',
                    options = [{'label': str(year), 'value': year} for year in range(2018, 2051)],
                    value=2024,
                )
            ], width = 6),
            dbc.Col([
                html.Label("Scenario"),
                dcc.Dropdown(
                    id='scenario-sankey-dropdown',
                    options= [{'label': s, 'value': s} for s in scenarios],
                    value= scenarios[0] if len(scenarios) > 0 else None,
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
        ])
    ])
    