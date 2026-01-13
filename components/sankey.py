import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dcc
# from utils.dataframe_melter import get_scenarios
from utils.get_data import get_scenarios, get_user_df
df_override = get_user_df()  # Replace with actual DataFrame if needed
scenarios = get_scenarios(df_override=df_override)
def sankey_layout ():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Year Range"),
                dcc.RangeSlider(
                    id='year-sankey-slider',
                    min= 2018, #all_data_melted['Year'].min(),
                    max= 2050, #all_data_melted['Year'].max()-1,
                    value=[2024, 2050],
                    marks={str(year): str(year) for year in range( 2020,2050,5)}, #range(all_data_melted['Year'].min(), all_data_melted['Year'].max(), 1)},
                    step=1
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Scenario"),
                dcc.Dropdown(
                    id='scenario-sankey-dropdown',
                    options= [{'label': s, 'value': s} for s in scenarios],
                    value= scenarios[0] if len(scenarios) > 0 else None,
                )
            ], width=6),
            dbc.Col([
                html.Label("Title"),
                dcc.Dropdown(
                    id="sankey_title_dropdown",
                    options=[
                        {'label': 'Final Energy to Demand', 'value': 0},
                        {'label': 'Primary Energy to Final Energy', 'value': 1}
                    ],
                    value=1
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
    