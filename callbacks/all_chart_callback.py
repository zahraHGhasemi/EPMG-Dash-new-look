from dash import Input, Output, State, ctx, no_update
# from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
# from utils.get_data import get_filtered_df, get_user_df
# from utils.plot_chart import plot_chart
# from utils.unit_handler import unit_detect, dict_unit
from dash import dcc, no_update
from urllib.parse import urlencode
from flask import has_request_context
from config.constants import CATEGORY_DICT
from data_provider.sql_data import SQLDataProvider
options_list = ['kt', 'PJ'] 
from auth.models import db
from urllib.parse import urlparse, parse_qs

session = db.session
def register_all_chart_callbacks(app, provider = SQLDataProvider(session=session)):
    
    @app.callback(
        Output("url", "href"),
        Input("url", "href"),
        prevent_initial_call=True
    )
    def ensure_study_in_url(href):
        if not href:
            return no_update

        parsed = urlparse(href)
        query = parse_qs(parsed.query)

        if "study_id" in query:
            return no_update

        latest = provider.get_latest_recent_study()
        if not latest:
            return no_update

        new_query = urlencode({"study_id": latest.id})
        return f"{parsed.path}?{new_query}"
    

    @app.callback(
        Output("scenario-chart-dropdown", "options"),
        Output("scenario-chart-dropdown", "value"),
        Input("url", "href")
    )
    def update_scenario_dropdown(href):
        if not href:
            return [], None

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return [], None

        scenarios = provider.get_scenarios_for_study(int(study_id))

        options = [{"label": s.name, "value": s.name} for s in scenarios]
        value = options[0]["value"] if options else None

        return options, value
        
        # scenarios = sorted(provider.get_scenarios())
        # value = scenarios[0] if scenarios else None
        # options = [{"label": s, "value": s} for s in scenarios]

        # return options, value
    @app.callback(
        Output('category-dropdown', 'options'),
        Output('category-dropdown', 'value'),
        Input('tabs', 'value')  # just a dummy input to trigger on load 
    )
    def update_category_options(tab_value):
        # df_override = None
        # if data_mode == "user" and has_request_context():
        #     df_override = get_user_df()
        # # Logic to get categories
        # categories = get_categories(df_override=df_override)
        categories = provider.get_categories()
        if 'SYS' in categories:
            value = 'SYS'
        else:
            value = categories[0] if categories else None
        return [{"label": CATEGORY_DICT.get(cat, cat), "value": cat} for cat in categories], value
    
    @app.callback(
        Output('subcategory-dropdown', 'options'),
        Output('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value')
    )
    def update_subcategory_options(category):
        # df_override = None
        # if data_mode == "user" and has_request_context():
        #     df_override = get_user_df()
        # # Logic to get subcategories based on selected category
        # subcategories = get_subcategories(category, df_override=df_override)
        subcategories = provider.get_subcategories(category)
        if category == 'SYS' and 'Domestic CO₂ Emissions by Sector' in subcategories:
            value = 'Domestic CO₂ Emissions by Sector'
        else:
            value = subcategories[0] if subcategories else None
        return [{"label": sub, "value": sub} for sub in subcategories], value
    

    @app.callback(
        Output('unit-dropdown', 'options'),
        Output('unit-dropdown', 'value'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value')
    )
    def update_unit(table_name,category, scenario, year_range):
        # df_override = None
        # if data_mode == "user" and has_request_context():
        #     df_override = get_user_df()
        # table_id = get_table_id(table_name,category, df_override=df_override)
        # df = get_filtered_df(table_id, scenario, year_range, df_override=df_override)
        table_id = provider.get_table_id(table_name, category)
        # df_unit = provider.get_labels(table_id, scenario, year_range)
        df_unit = provider.get_labels(table_id)
        options =[]
        value = None
        # label = df['label'].iloc[0]
        label = df_unit[0] 
        if label == "PJ":
            options = ['PJ', 'TWh', 'ktoe']
        elif label == "kt":
            options =['kt', 'Mt']
        else:
            options = [label]

        value = options[0]
        return options, value
    
    
    # @app.callback(
    #     Output('selected-graph', 'figure'),
    #     Input('subcategory-dropdown', 'value'),
    #     Input('category-dropdown', 'value'),
    #     Input('scenario-chart-dropdown', 'value'),
    #     Input('year-slider', 'value'),
    #     Input('chart-type-dropdown', 'value'),
    #     Input('unit-dropdown', 'value')
    #     # Input('generate_btn', 'n_clicks'),
    #     # prevent_initial_call=True  
    # )
    # def update_graph(table_name,category, scenario, year_range, chart_types, unit):
    #     table_id = get_table_id(table_name,category)
    #     df = get_filtered_df(table_id, scenario, year_range)

    #     if unit in dict_unit.keys():
    #         df = unit_detect( unit, df)
    #     return plot_chart(df, chart_types)
    
    # @app.callback(
    #     Output("download-dataframe-csv", "data"),
    #     Input("btn-download", "n_clicks"),
    #     State('subcategory-dropdown', 'value'),
    #     State('category-dropdown', 'value'),
    #     State('scenario-chart-dropdown', 'value'),
    #     State('year-slider', 'value'),
    #     State('chart-type-dropdown', 'value'),
    #     prevent_initial_call=True
    # )
    # def download_current_chart(n_clicks, table_name,category, scenario, year_range, chart_types):
    #     table_id = get_table_id(table_name,category)
    #     df = get_filtered_df(table_id, scenario, year_range)
    #     return dcc.send_data_frame(df.to_csv, f"chart_data_{year_range}.csv", index=False)
    
    