import dash_bootstrap_components as dbc
from dash import html, dcc

from data_provider.sql_data import SQLDataProvider
# from utils.dataframe_melter import get_scenarios
# from utils.get_data import get_scenarios
# scenarios = get_scenarios()
from utils.dashboard_settings import get_dashboard_settings


def overview_layout():
    settings = get_dashboard_settings()
    start_year = settings["start_year"]
    default_start_year = settings["default_start_year"]
    default_end_year = settings["default_end_year"]
    end_year = settings["end_year"]
    overview_metric = settings["overview_metric"]
    overview_chart_type = settings["overview_chart_type"]

    return dbc.Container([
    
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
                dcc.Dropdown(
                    id='scenario-dropdown',
                    persistence=True,
                    persistence_type='session'
                )
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
                html.Label("Start Year", className="control-label"),
                dcc.Dropdown(
                    id='start-year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in range(start_year, end_year + 1)],
                    value=default_start_year,
                    persistence=True,
                    persistence_type='session'
                )
        ], width =1),
        dbc.Col([
                html.Label("End Year", className="control-label"),
                dcc.Dropdown(
                    id='end-year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in range(start_year, end_year + 1)],
                    value=default_end_year,
                    persistence=True,
                    persistence_type='session'
                )
        ], width =1),
        dbc.Col([
                html.Label("Metric", className="control-label"),
                dcc.Dropdown(
                    id='metric-dropdown',
                    options=['FEC', 'Import', 'Renewable'],
                    value=overview_metric,
                    persistence=True,
                    persistence_type='session'
                ) 
        ], width=4),
        dbc.Col([
                html.Label("Chart Type", className="control-label"),
                dcc.Dropdown(
                    id='chart-type-overview-dropdown',
                    options= {'bar': 'Bar', 'pie': 'Pie'},
                    value=overview_chart_type,
                    persistence=True,
                    persistence_type='session'
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
