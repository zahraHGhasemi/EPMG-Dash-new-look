import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from callbacks.compare_callback import register_compare_chart_callbacks
from callbacks.all_chart_callback import register_all_chart_callbacks 
from callbacks.tab_content_callbacks import register_tab_content_callbacks
from callbacks.sankey_callback import register_sankey_callback
from data_provider.dataframe_data import DataFrameProvider
# Initialize user Dash
def init_user_dash(server):
    app = dash.Dash(__name__, server=server, url_base_pathname="/user/dashboard/",
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True)

    app.layout = html.Div([
        dbc.Row([       
            dbc.Col([
                dcc.Tabs(id ='tabs', value = 'compare-scenarios', children =[
                    # dcc.Tab(label = 'About', value = 'about'),
                    # dcc.Tab(label='Overview', value='overview'),
                    # dcc.Tab(label='Chart Detail', value='all-charts'),
                    dcc.Tab(label='Charts', value='compare-scenarios'),
                    dcc.Tab(label= "Sankey Diagram", value = 'sankey')
                ]),
        html.Div(id='tab-content', children='Loading...'),
            ], width=12)
        ])
        
    ])
    provider = DataFrameProvider()
    register_compare_chart_callbacks(app, provider= provider)
    register_all_chart_callbacks(app, provider= provider)
    register_sankey_callback(app, provider= provider)
    register_tab_content_callbacks(app)
    return app












# import dash
# from dash import html, dcc, dash_table
# import dash_bootstrap_components as dbc
# import pandas as pd

# from utils.get_data import get_user_df


# def init_user_dash(server):
#     app = dash.Dash(
#         __name__,
#         server=server,
#         url_base_pathname="/user/dash/",
#         external_stylesheets=[dbc.themes.BOOTSTRAP],
#         suppress_callback_exceptions=True,
#     )

#     app.layout = html.Div(
#         [
#             html.H2("User Uploaded Data – Debug View", className="mb-3"),

#             html.Div(id="user-data-info", className="mb-3"),

#             dash_table.DataTable(
#                 id="user-data-table",
#                 page_size=20,
#                 style_table={"overflowX": "auto", "maxHeight": "600px", "overflowY": "auto"},
#                 style_cell={
#                     "textAlign": "left",
#                     "fontSize": "13px",
#                     "whiteSpace": "normal",
#                 },
#             ),
#         ],
#         style={"padding": "30px"},
#     )

#     @app.callback(
#         dash.Output("user-data-info", "children"),
#         dash.Output("user-data-table", "data"),
#         dash.Output("user-data-table", "columns"),
#         dash.Input("user-data-table", "id"),  # dummy trigger
#     )
#     def load_user_data(_):
#         df = get_user_df()

#         if df is None or df.empty:
#             return (
#                 dbc.Alert("❌ No user data found in session", color="danger"),
#                 [],
#                 [],
#             )

#         info = dbc.Alert(
#             f"✅ Loaded user data: {df.shape[0]} rows × {df.shape[1]} columns",
#             color="success",
#         )
#         print(df['Scenario'].unique(), "---user data scenarios---")
#         return (
#             info,
#             df.head(200).to_dict("records"),
#             [{"name": c, "id": c} for c in df.columns],
#         )

#     return app
