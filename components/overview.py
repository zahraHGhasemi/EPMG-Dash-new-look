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
    overview_metrics = settings.get("overview_metrics", [])
    metric_options = [
        {"label": metric["title"], "value": metric["title"]}
        for metric in overview_metrics
    ]
    if not metric_options and overview_metric:
        metric_options = [{"label": overview_metric, "value": overview_metric}]
    metric_values = {option["value"] for option in metric_options}
    default_metric_value = overview_metric if overview_metric in metric_values else (metric_options[0]["value"] if metric_options else None)

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
                    clearable=False,
                    persistence=True,
                    persistence_type='session'
                )
                
        ], width=6),
       
        dbc.Col([
                html.Label("Metric", className="control-label"),
                dcc.Dropdown(
                    id='metric-dropdown',
                    clearable=False,
                    options=metric_options,
                    value=default_metric_value,
                    persistence=True,
                    persistence_type='session'
                ) 
        ], width=6),
        dbc.Col([
                html.Label("Start Year", className="control-label"),
                dcc.Dropdown(
                    id='start-year-dropdown',
                    clearable=False,
                    options=[{'label': str(year), 'value': year} for year in range(start_year, end_year + 1)],
                    value=default_start_year,
                    persistence=True,
                    persistence_type='session'
                )
        ], width =3),
        dbc.Col([
                html.Label("End Year", className="control-label"),
                dcc.Dropdown(
                    id='end-year-dropdown',
                    clearable=False,
                    options=[{'label': str(year), 'value': year} for year in range(start_year, end_year + 1)],
                    value=default_end_year,
                    persistence=True,
                    persistence_type='session'
                )
        ], width =3),
    
        
        dbc.Col([
                html.Label("Unit"),
                dcc.Dropdown(
                    id = "unit-dropdown-overview",
                    clearable= False,
                    options = [],
                    value = None,
                    persistence=True,
                    persistence_type='session'
                )
        ], width=3),
        dbc.Col([
                html.Label("Chart Type", className="control-label"),
                dcc.Dropdown(
                    id='chart-type-overview-dropdown',
                    clearable=False,
                    options= {'bar': 'Bar', 'pie': 'Pie'},
                    value=overview_chart_type,
                    persistence=True,
                    persistence_type='session'
                ),
        ], width=3)
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
