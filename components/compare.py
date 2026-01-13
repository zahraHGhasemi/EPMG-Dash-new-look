from dash import html
from dash import dcc
from utils.plot_chart import plot_chart
import dash_bootstrap_components as dbc
# from utils.dataframe_melter import get_scenarios
from components.all_charts import options_layout
from utils.get_data import get_scenarios,get_user_df
from data_provider.dataframe_data import DataFrameProvider
from data_provider.sql_data import SQLDataProvider
# df_override = get_user_df()  # Replace with actual DataFrame if needed
# scenarios = get_scenarios(df_override=df_override)


def compare_charts_layout():
    base = options_layout()
    base.children.append(
        dbc.Accordion([
            dbc.AccordionItem([
                dbc.Row([
                    dbc.Col([
                        html.Label("Compare Mode"),
                        dbc.RadioItems(
                            id = 'compare-radio',
                            options=[
                                {'label': 'Yes', 'value': 1},
                                {'label': 'No', 'value': 0},
                            ],
                            value=0,  # Default selection
                            inline=True
                        )
                    ],width = 3),
                    dbc.Col([
                        html.Label("Compare Scenario", className="control-label"),
                        dcc.Dropdown(
                            id='compare-scenario-dropdown',
                            # options=[{'label': s, 'value': s} for s in scenarios],
                            # value=scenarios[1] if len(scenarios) > 1 else None,
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
                    ],width = 3)
                ])
            ], title = 'Compare')
        ], start_collapsed=True,)

    
    )
    base.children.append(
        dbc.Row([
            dbc.Accordion(
                children = [
                    dbc.AccordionItem([
                        html.Div([], id = 'color-accordion' )
                    ],title = 'Color')
                ],
                start_collapsed=True,
                always_open=False
            )
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
    base.children.append(
        dbc.Row([
                dbc.Col(html.Hr(), width=10),
                 dbc.Col([
                    dbc.Button(
                        "⬇️ Download CSV",
                        id="btn-download",
                        color="primary",
                        className="ms-2"
                    ),
                    dcc.Download(id="download-dataframe-csv")
                ], width="auto"),
            ], align="center", className="mb-3"),   
    )
    return base