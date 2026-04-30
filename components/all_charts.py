from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from utils.dashboard_settings import get_dashboard_settings

def options_layout():
    """Generate the layout for the chart options, including dropdowns for scenario, sector, subsector, chart type, and unit."""
    settings = get_dashboard_settings()
    start_year = settings["start_year"]
    end_year = settings["end_year"]
    default_start_year = settings["default_start_year"]
    default_end_year = settings["default_end_year"]

    return dbc.Container([
    dbc.Row([
            dbc.Col([
                html.Label("Year Range"),
                dcc.RangeSlider(
                    id='year-slider',
                    min=start_year,
                    max=end_year,
                    value=[default_start_year, default_end_year],
                    marks={str(year): str(year) for year in range(start_year, end_year + 1, 5)},
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
                    id='scenario-chart-dropdown',
                    clearable= False,
                    persistence=True,
                    persistence_type='session',
                    
                )
            ], width=4),
            
            dbc.Col([
                html.Label("Sector"),
                dcc.Dropdown(
                    id='category-dropdown',
                    clearable= False,
                    persistence=True,
                    persistence_type='session',
                    
                )
            ], width=4),
            dbc.Col([
                html.Label('Subsector'),
                dcc.Dropdown(
                    id='subcategory-dropdown',
                    clearable= False,
                    options=[],  
                    value= None,  
                    persistence=True,
                    persistence_type='session'
                )
            ], width=4)

        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Chart Types"),
                dcc.Dropdown(
                    id='chart-type-dropdown',
                    clearable= False,
                    options= {'bar': 'Bar', 'line': 'Line', 'area': 'Area'},
                    value= 'bar',
                    persistence=True,
                    persistence_type='session'
                )
            ], width=6),
            dbc.Col([
                html.Label("Unit"),
                dcc.Dropdown(
                    id = "unit-dropdown",
                    clearable= False,
                    options = [],
                    value = None,
                    persistence=True,
                    persistence_type='session'
                )
            ], width=6)
        ])
    ])
