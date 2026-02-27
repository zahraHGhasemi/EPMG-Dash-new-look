from urllib.parse import parse_qs, urlparse
from dash import Input, Output, State
import plotly.express as px
# from utils.dataframe_melter import get_data_melted
from data_provider.sql_data import SQLDataProvider
from utils.plot_chart import plot_pie_chart, plot_bar_chart, plot_two_pie_charts_px, plot_two_bar_charts_px
from utils.dashboard_settings import get_dashboard_settings
def register_overview_callbacks(app, provider):
    @app.callback(
        Output('scenario-dropdown', 'options'),
        Output('scenario-dropdown', 'value'),
    #     Input('tabs', 'value') 
        Input("url", "href"),
        State("scenario-dropdown", "value")
    )
    def update_scenario_dropdown(href, current_value):
        if not href:
            return [], None

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return [], None

        try:
            study_id = int(study_id)
        except (TypeError, ValueError):
            return [], None

        scenarios = provider.get_scenarios_for_study(study_id)
        options = [{"label": s.name, "value": s.name} for s in scenarios]
        configured = get_dashboard_settings().get("default_scenario")
        option_values = {opt["value"] for opt in options}
        if current_value in option_values:
            value = current_value
        elif configured in option_values:
            value = configured
        else:
            value = options[0]["value"] if options else None
        return options, value
    # def update_scenario_options(tab_value):
    #     scenarios = sorted(provider.get_scenarios())
    #     print(scenarios, 'scenarios in overview callback')
    #     value = scenarios[0] if len(scenarios) > 0 else None
    #     options = [{"label": s, "value": s} for s in scenarios]
    #     return options, value
    
    @app.callback(
        Output('overview-chart', 'figure'),
        Input('scenario-dropdown', 'value'),
        Input('start-year-dropdown', 'value'),
        Input('end-year-dropdown', 'value'),
        Input('metric-dropdown', 'value'),
        Input('chart-type-overview-dropdown', 'value')
    )
    def update_overview_chart(scenario, year_start, year_end, metric, chart_type):
        # data_melted_base = get_data_melted(scenario, [year_start, year_start])
        # all_data_melted = get_data_melted(scenario, [year_end, year_end])
        renewable_list = ['PWR-WIN-OF', "PWR-SOL","PWR-WIN-ON","PWR-BIO", "PWR-HYD", "PWR-OCE"]
        table_id_SYS_FEC_Fuel = provider.get_table_id_by_name('SYS_FEC_Fuel')
        table_id_SYS_NRG_Import = provider.get_table_id_by_name('SYS_NRG-Import')
        table_id_PWR_Gen_ELCC = provider.get_table_id_by_name('PWR_Gen-ELCC')
        label = "Value"
        if metric == 'FEC':
            data_base = provider.get_filtered_df(table_id_SYS_FEC_Fuel, scenario, [year_start, year_start])
            data_selected = provider.get_filtered_df(table_id_SYS_FEC_Fuel, scenario, [year_end, year_end])
            # data_base = data_melted_base[data_melted_base['tableName'] == 'SYS_FEC_Fuel']
            # data_selected = all_data_melted[all_data_melted['tableName'] == 'SYS_FEC_Fuel']
            label = provider.get_labels(table_id_SYS_FEC_Fuel)[0]
        
        elif metric == 'Import':
            data_base = provider.get_filtered_df(table_id_SYS_NRG_Import, scenario, [year_start, year_start])
            data_selected = provider.get_filtered_df(table_id_SYS_NRG_Import, scenario, [year_end, year_end])
            # data_base = data_melted_base[data_melted_base['tableName'] == 'SYS_NRG-Import']
            # data_selected = all_data_melted[all_data_melted['tableName'] == 'SYS_NRG-Import']
            label = provider.get_labels(table_id_SYS_NRG_Import)[0]

        elif metric == 'Renewable':
            data_base = provider.get_filtered_df(table_id_PWR_Gen_ELCC, scenario, [year_start, year_start])
            data_selected = provider.get_filtered_df(table_id_PWR_Gen_ELCC, scenario, [year_end, year_end])
            data_base = data_base[data_base['seriesName'].isin(renewable_list)]
            data_selected = data_selected[data_selected['seriesName'].isin(renewable_list)]
            label = provider.get_labels(table_id_PWR_Gen_ELCC)[0]
            # data_base = data_melted_base[(data_melted_base['tableName'] == 'PWR_Gen-ELCC')& 
            #                                     (data_melted_base['seriesName'].isin(renewable_list))]
            # data_selected = all_data_melted[(all_data_melted['tableName'] == 'PWR_Gen-ELCC')& 
            #                                    (all_data_melted['seriesName'].isin(renewable_list))]
        if chart_type == 'pie':
            fig = plot_two_pie_charts_px(data_base, year_start, data_selected, year_end, metric, label)
        elif chart_type == 'bar':
            fig = plot_two_bar_charts_px(data_base, year_start, data_selected, year_end, metric, label)

        return fig
