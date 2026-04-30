from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from components.all_charts import options_layout



def compare_charts_layout():
    """Generate the layout for the Compare Charts section and color layout accordion in the charts tab, which includes options for selecting scenarios to compare and a graph to display the comparison.
    It also includes a download button for exporting the comparison data as CSV."""
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
                            value=0,  
                            inline=True,
                            persistence=True,
                            persistence_type='session'
                        )
                    ],width = 3),
                    dbc.Col([
                        html.Label("Compare Scenario", className="control-label"),
                        dcc.Dropdown(
                            id='compare-scenario-dropdown',
                            clearable=False,
                            persistence=True,
                            persistence_type='session',
                            
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
                            value='no',  
                            inline=True,
                            persistence=True,
                            persistence_type='session'
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
                    ],title = 'Colour')
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
