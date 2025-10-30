from dash import Input, Output, State, ctx, no_update
from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
from utils.get_data import get_filtered_df
from utils.plot_chart import plot_chart
from utils.unit_handler import unit_detect
from dash import dcc


acceptable_units = ["PJ", "kt","GW"]
options_list = ['K', 'M', 'G', 'T', 'P'] 

def register_all_chart_callbacks(app):
    @app.callback(
        Output('subcategory-dropdown', 'options'),
        Output('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value')
    )
    def update_subcategory_options(category):
        # Logic to get subcategories based on selected category
        subcategories = get_subcategories(category)
        # print(subcategories, 'subcategory list')
        if category == 'System':
            value = 'Domestic CO2 Emissions by Sector'
        else:
            value = subcategories[0] if subcategories else None
        # print(value, 'VALUE')
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
        table_id = get_table_id(table_name,category)
        df = get_filtered_df(table_id, scenario, year_range)
        options =[]
        value = None
        label = df['label'].iloc[0]
        print(label, "label")
        if label in acceptable_units:
            label_unit = label[1]
            options = {option: option + label_unit  for option in options_list}
            print(options)
            value = label[0].upper()
            print(value)
        else:
            options = [label]
            value = label
        print(options, value, "option and value")
        return options, value
    
    
    @app.callback(
        Output('selected-graph', 'figure'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value'),
        Input('chart-type-dropdown', 'value'),
        Input('unit-dropdown', 'value')
        # Input('generate_btn', 'n_clicks'),
        # prevent_initial_call=True  
    )
    def update_graph(table_name,category, scenario, year_range, chart_types, unit):
        table_id = get_table_id(table_name,category)
        df = get_filtered_df(table_id, scenario, year_range)

        if unit in options_list:
            print("here to track")
            label = df['label'].iloc[0]
            df = unit_detect(label, unit, df)
            print(df['label'].iloc[0], "here in unit")
        return plot_chart(df, chart_types)
    
    @app.callback(
        Output("download-dataframe-csv", "data"),
        Input("btn-download", "n_clicks"),
        State('subcategory-dropdown', 'value'),
        State('category-dropdown', 'value'),
        State('scenario-chart-dropdown', 'value'),
        State('year-slider', 'value'),
        State('chart-type-dropdown', 'value'),
        prevent_initial_call=True
    )
    def download_current_chart(n_clicks, table_name,category, scenario, year_range, chart_types):
        table_id = get_table_id(table_name,category)
        df = get_filtered_df(table_id, scenario, year_range)
        return dcc.send_data_frame(df.to_csv, f"chart_data_{year_range}.csv", index=False)
    
    