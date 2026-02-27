from dash import html
from dash import dcc
# from utils.plot_chart import plot_chart
import dash_bootstrap_components as dbc
# from utils.dataframe_melter import get_scenarios
# from utils.get_data import get_scenarios, get_user_df
from utils.dashboard_settings import get_dashboard_settings
# df_override = get_user_df()  # Replace with actual DataFrame if needed
# scenarios = get_scenarios(df_override=df_override)
# print("Available scenarios:", scenarios)

def options_layout():
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
                    id='scenario-chart-dropdown',
                    clearable= False,
                    persistence=True,
                    persistence_type='session',
                    # options= [{'label': s, 'value': s} for s in scenarios],
                    # value= scenarios[0] if len(scenarios) > 0 else None,
                )
            ], width=4),
            
            dbc.Col([
                html.Label("Sector"),
                dcc.Dropdown(
                    id='category-dropdown',
                    clearable= False,
                    persistence=True,
                    persistence_type='session',
                    # options= ['System', 'Supply', 'Power', 'Transport', 'Residential', 'Services',
                    #             'Industry', 'Agriculture'],
                    # value = 'System',
                )
            ], width=4),
            dbc.Col([
                html.Label('Subsector'),
                dcc.Dropdown(
                    id='subcategory-dropdown',
                    clearable= False,
                    options=[],  # To be populated based on category selection
                    value= None,  # Default value
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
def all_charts_layout():
    return (
        dbc.Container([
            options_layout(),
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
            
            dbc.Row([
                dbc.Col(
                    dbc.Spinner(
                        dcc.Graph(id='selected-graph', style={'height': '600px'}),
                        color="primary",      # spinner color
                        size="lg",            # spinner size
                        type="border"         # or "grow"
                    ),
                    width=12
                )
            ])
        ])        
    )
