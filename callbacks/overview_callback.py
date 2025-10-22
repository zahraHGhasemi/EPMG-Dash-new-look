from dash import Input, Output
import plotly.express as px
from utils.dataframe_melter import get_data_melted
from utils.plot_chart import plot_pie_chart, plot_bar_chart, plot_two_pie_charts_px, plot_two_bar_charts_px

def register_overview_callbacks(app):#, all_data_melted):
    # @app.callback(
    #     Output('chart-base', 'figure'),
    #     Output('chart-selected-year', 'figure'),
    #     Input('scenario-dropdown', 'value'),
    #     Input('start-year-dropdown', 'value'),
    #     Input('end-year-dropdown', 'value'),
    #     Input('metric-dropdown', 'value'),
    #     Input('chart-type-overview-dropdown', 'value')
    # )
    # def update_overview_chart(scenario, year_start, year_end, metric, chart_type):
    #     data_melted_base = get_data_melted(scenario, [year_start, year_start])
    #     all_data_melted = get_data_melted(scenario, [year_end, year_end])
    #     renewable_list = ['PWR-WIN-OF', "PWR-SOL","PWR-WIN-ON","PWR-BIO", "PWR-HYD", "PWR-OCE"]

    #     if metric == 'FEC':
    #         data_base = data_melted_base[data_melted_base['tableName'] == 'SYS_FEC_Fuel']
    #         data_selected = all_data_melted[all_data_melted['tableName'] == 'SYS_FEC_Fuel']
    #     elif metric == 'Import':
    #         data_base = data_melted_base[data_melted_base['tableName'] == 'SYS_NRG-Import']
    #         data_selected = all_data_melted[all_data_melted['tableName'] == 'SYS_NRG-Import']
    #     elif metric == 'Renewable':
    #         data_base = data_melted_base[(data_melted_base['tableName'] == 'PWR_Gen-ELCC')& 
    #                                             (data_melted_base['seriesName'].isin(renewable_list))]
    #         data_selected = all_data_melted[(all_data_melted['tableName'] == 'PWR_Gen-ELCC')& 
    #                                            (all_data_melted['seriesName'].isin(renewable_list))]
    #     if chart_type == 'pie':
    #         fig_base = plot_pie_chart(data_base, year_start, metric)
    #         fig_selected = plot_pie_chart(data_selected, year_end, metric)
    #     elif chart_type == 'bar':
    #         fig_base = plot_bar_chart(data_base, year_start, metric)
    #         fig_selected = plot_bar_chart(data_selected, year_end, metric)
        
    #     return fig_base, fig_selected
    @app.callback(
        Output('overview-chart', 'figure'),
        Input('scenario-dropdown', 'value'),
        Input('start-year-dropdown', 'value'),
        Input('end-year-dropdown', 'value'),
        Input('metric-dropdown', 'value'),
        Input('chart-type-overview-dropdown', 'value')
    )
    def update_overview_chart(scenario, year_start, year_end, metric, chart_type):
        data_melted_base = get_data_melted(scenario, [year_start, year_start])
        all_data_melted = get_data_melted(scenario, [year_end, year_end])
        renewable_list = ['PWR-WIN-OF', "PWR-SOL","PWR-WIN-ON","PWR-BIO", "PWR-HYD", "PWR-OCE"]

        if metric == 'FEC':
            data_base = data_melted_base[data_melted_base['tableName'] == 'SYS_FEC_Fuel']
            data_selected = all_data_melted[all_data_melted['tableName'] == 'SYS_FEC_Fuel']
        elif metric == 'Import':
            data_base = data_melted_base[data_melted_base['tableName'] == 'SYS_NRG-Import']
            data_selected = all_data_melted[all_data_melted['tableName'] == 'SYS_NRG-Import']
        elif metric == 'Renewable':
            data_base = data_melted_base[(data_melted_base['tableName'] == 'PWR_Gen-ELCC')& 
                                                (data_melted_base['seriesName'].isin(renewable_list))]
            data_selected = all_data_melted[(all_data_melted['tableName'] == 'PWR_Gen-ELCC')& 
                                               (all_data_melted['seriesName'].isin(renewable_list))]
        if chart_type == 'pie':
            fig = plot_two_pie_charts_px(data_base, year_start, data_selected, year_end, metric)
        elif chart_type == 'bar':
            fig = plot_two_bar_charts_px(data_base, year_start, data_selected, year_end, metric)

        return fig