from dash import html
from dash import dcc
from utils.plot_chart import plot_chart
import dash_bootstrap_components as dbc
from utils.dataframe_melter import get_scenarios
from components.all_charts import options_layout

scenarios = get_scenarios()

def compare_charts_layout():
    base = options_layout()
    base.children.append(
        dbc.Row([
            dbc.Col([
                html.Label("Compare Scenario", className="control-label"),
                dcc.Dropdown(
                    id='compare-scenario-dropdown',
                    options=[{'label': s, 'value': s} for s in scenarios],
                    value=scenarios[1] if len(scenarios) > 1 else None,
                ),
                ], width=6),
            dbc.Col([
                html.Label("Show difference", className="control-label"),
                dbc.RadioItems(
                    id='difference-radio',
                    options=[
                        {'label': 'Yes', 'value': 'yes'},
                        {'label': 'No', 'value': 'no'},
                    ],
                    value='no',  # Default selection
                    inline=True
                ) 
            ])
        ])
    )
    base.children.append(
        dbc.Row([
            dbc.Col(
            [
                dbc.Spinner(
                    dcc.Graph(
                        id='compare-chart',
                        style={'height': '600px'},
                        config={'responsive': True}
                    ),
                    color="primary",      # spinner color
                    size="lg",            # spinner size
                    type="border"         # or "grow"
                )
                # dcc.Graph(id='compare-chart',
                #           style={'height': '600px'},
                #         config={'responsive': True})
            ])
        ])
    )
    return base