import dash_bootstrap_components as dbc
from dash import html, dcc

from data_provider.sql_data import SQLDataProvider
# from utils.dataframe_melter import get_scenarios
# from utils.get_data import get_scenarios
# scenarios = get_scenarios()
DEFAULT_YEAR = 2024
DEFAULT_YEAR_END = 2050


# def get_scenario_dropdown():
#     try:
#         # scenarios = get_scenarios()
#         scenarios = SQLDataProvider(table_name="scenarios").get_scenarios()
#         if not scenarios:
#             return dcc.Dropdown(
#                 id='scenario-dropdown',
#                 options=[],
#                 placeholder="No scenarios found",
#                 disabled=True
#             )
#         return dcc.Dropdown(
#             id='scenario-dropdown',
#             options=[{'label': s, 'value': s} for s in scenarios],
#             value=scenarios[0],
#         )
#     except Exception as e:
#         return dcc.Dropdown(
#             id='scenario-dropdown',
#             options=[],
#             placeholder="Error loading scenarios",
#             disabled=True
#         )
from config.constants import START_YEAR, END_YEAR
overview_layout = dbc.Container([
    
    dbc.Row([
        dbc.Col([
            html.H3("Description", className="mb-4"),
            html.P("This overview provides insights into the selected scenario's key metrics over the " \
            "specified year range. Users can select different scenarios, years, metrics, and chart types" \
            " to visualise the data effectively." ),
            html.Br(),
        ], width=12),
          
    
        dbc.Col([
                html.Label("Scenario", className="control-label"),
                dcc.Dropdown(id='scenario-dropdown')
                # get_scenario_dropdown()
                # dcc.Dropdown(
                #     id='scenario-dropdown',
                #     options=[{'label': s, 'value': s} for s in scenarios],
                #     value=scenarios[0] if len(scenarios) > 0 else None,
                #     # placeholder="Select a scenario...",
                #     # className="dropdown"
                # )
        ], width=4),
        dbc.Col([
                html.Label("Start year", className="control-label"),
                dcc.Dropdown(
                    id='start-year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in range(START_YEAR, END_YEAR + 1)],
                    value=START_YEAR
                )
        ], width =1),
        dbc.Col([
                html.Label("End year", className="control-label"),
                dcc.Dropdown(
                    id='end-year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in range(START_YEAR, END_YEAR + 1)],
                    value=END_YEAR
                )
        ], width =1),
        dbc.Col([
                html.Label("Metric", className="control-label"),
                dcc.Dropdown(
                    id='metric-dropdown',
                    options=['FEC', 'Import', 'Renewable'],
                    value='FEC'
                ) 
        ], width=4),
        dbc.Col([
                html.Label("Chart Type", className="control-label"),
                dcc.Dropdown(
                    id='chart-type-overview-dropdown',
                    options= {'bar': 'Bar', 'pie': 'Pie'},
                    value= 'pie',
                ),
        ], width=2)
    ], className="mb-4"),
   
    dbc.Row([
        dbc.Col(
        [
            dbc.Spinner(
                dcc.Graph(id='overview-chart',
                    style={'height': '500px'},
                    config={'responsive': True}
                ),
                color="primary",      # spinner color
                size="lg",            # spinner size
                type="border"         # or "grow"
            )
            
            
        ],
            md=12,  # full width on medium+ screens
        )
        
    ])

    
])