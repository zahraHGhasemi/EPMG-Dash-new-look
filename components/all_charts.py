from dash import html
from dash import dcc
from utils.plot_chart import plot_chart
import dash_bootstrap_components as dbc
from utils.dataframe_melter import get_scenarios

scenarios = get_scenarios()
def options_layout():
    return dbc.Container([
    dbc.Row([
            dbc.Col([
                html.Label("Year Range"),
                dcc.RangeSlider(
                    id='year-slider',
                    min= 2018, #all_data_melted['Year'].min(),
                    max= 2050, #all_data_melted['Year'].max()-1,
                    value=[2018, 2050],
                    marks={str(year): str(year) for year in range( 2018,2050,1)}, #range(all_data_melted['Year'].min(), all_data_melted['Year'].max(), 1)},
                    step=1
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Scenario"),
                dcc.Dropdown(
                    id='scenario-chart-dropdown',
                    options= [{'label': s, 'value': s} for s in scenarios],
                    value= scenarios[0] if len(scenarios) > 0 else None,
                )
            ], width=3),
            dbc.Col([
                html.Label("Chart Types"),
                dcc.Dropdown(
                    id='chart-type-dropdown',
                    options= {'bar': 'Bar', 'line': 'Line', 'area': 'Area'},
                    value= 'bar',
                )
            ], width=3),
            dbc.Col([
                html.Label("Sector"),
                dcc.Dropdown(
                    id='category-dropdown',
                    options= ['System', 'Supply', 'Power', 'Transport', 'Residential', 'Services',
                                'Industry', 'Agriculture'],
                    value = 'System',
                )
            ], width=3),
            dbc.Col([
                html.Label('Subsector'),
                dcc.Dropdown(
                    id='subcategory-dropdown',
                    options=[],  # To be populated based on category selection
                    value= None,  # Default value
                )
            ], width=3)

        ])
    ])
def all_charts_layout():
    return (
        # dbc.Row([
        #     html.Label("Year Range:"),
        #         dcc.RangeSlider(
        #             id='year-slider',
        #             min= 2018, #all_data_melted['Year'].min(),
        #             max= 2050, #all_data_melted['Year'].max()-1,
        #             value=[2018, 2050],
        #             marks={str(year): str(year) for year in range( 2018,2050,1)}, #range(all_data_melted['Year'].min(), all_data_melted['Year'].max(), 1)},
        #             step=1
        #         ),
        #     dbc.Col([
        #         html.Div([
                    
        #             html.Label("Chart Types:"),
        #             dbc.RadioItems(
        #                 id='chart-type-radio',
        #                 options=[
        #                     {'label': 'Bar', 'value': 'bar'},
        #                     {'label': 'Line', 'value': 'line'},
        #                     {'label': 'Area', 'value': 'area'},
        #                 ],
        #                 value='bar',  # Default selection
        #                 # inline=True
        #             ),
        #             html.Label("Sector:"),
        #             dbc.RadioItems(
        #                 id="category-radio",
        #                 options = ['Supply', 'Power', 'Transport', 'Residential', 'Services',
        #                             'Industry', 'Agriculture', 'System'],
        #                 value = 'Supply',
        #                 labelStyle={"display": "block"},
        #                 # inline=True
        #             ),
        #             html.Label('Subsector:'),
        #             dbc.RadioItems(
        #                 id='subcategory-radio',
        #                 options=[],  # To be populated based on category selection
        #                 value='Biodiesel Supply by Source',  # Default value
        #                 # inline=True
        #             ),
        #             html.Button("Generate Chart", id="generate_btn", n_clicks=1)
        #         ])
        #     ], width=2 ),
        #     dbc.Col(
        #         dcc.Graph(id='selected-graph', style={'height': '600px'}),
        #         width=10
        #     )
        # ])
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

            # html.Div([
            #     html.Label("Year Range:"),
            #     dcc.RangeSlider(
            #         id='year-slider',
            #         min= 2018, #all_data_melted['Year'].min(),
            #         max= 2050, #all_data_melted['Year'].max()-1,
            #         value=[2018, 2050],
            #         marks={str(year): str(year) for year in range( 2018,2050,1)}, #range(all_data_melted['Year'].min(), all_data_melted['Year'].max(), 1)},
            #         step=1
            #     ),
            #     html.Label("Chart Types:"),
            #     dbc.RadioItems(
            #         id='chart-type-radio',
            #         options=[
            #             {'label': 'Bar', 'value': 'bar'},
            #             {'label': 'Line', 'value': 'line'},
            #             {'label': 'Area', 'value': 'area'},
            #         ],
            #         value='bar',  # Default selection
            #         inline=True
            #     ),
            #     html.Label("Sector:"),
            #     dbc.RadioItems(
            #         id="category-radio",
            #         options = ['Supply', 'Power', 'Transport', 'Residential', 'Services',
            #                     'Industry', 'Agriculture', 'System'],
            #         value = 'Supply',
            #         labelStyle={"display": "block"},
            #         inline=True
            #     ),
            #     html.Label('Subsector:'),
            #     dbc.RadioItems(
            #         id='subcategory-radio',
            #         options=[],  # To be populated based on category selection
            #         value='Biodiesel Supply by Source',  # Default value
            #         inline=True
            #     ),
            #     html.Button("Generate Chart", id="generate_btn", n_clicks=1),

            #     dcc.Graph(id='selected-graph')
            # ]),
            
        
    )
