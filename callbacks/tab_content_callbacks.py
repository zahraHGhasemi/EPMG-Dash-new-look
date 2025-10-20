from dash import Input, Output
from components.overview import overview_layout
# from components.supply import supply_layout
# from components.power import power_layout
# from components.sector import sector_layout
# from components.search import search_layout
# from components.emissionCO2 import emissionCO2_layout 
# from callbacks.overview_callback import register_overview_callbacks
# from callbacks.supply_callback import register_supply_callbacks
# from callbacks.power_callback import register_power_callbacks
# from callbacks.emissionCO2_callback import register_emissionCO2_callback
# from callbacks.sector_callback import register_sector_callbacks
# from callbacks.subsector_callbacks.subsector_overview_callback import register_subsector_overview_callback
# from callbacks.subsector_callbacks.subsector_transport_callback import register_subsector_transport_callback
# from callbacks.subsector_callbacks.subsector_residential_callback import register_subsector_residential_callback
# from callbacks.subsector_callbacks.subsector_services_callback import register_subsector_services_callback
# from callbacks.subsector_callbacks.subsector_industry_callback import register_subsector_industry_callback
# from callbacks.search_callback import register_search_callbacks
from components.all_charts import all_charts_layout
from components.compare import compare_charts_layout
from utils.dataframe_melter import get_data_melted
def register_tab_content_callbacks(app):
    @app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value'),
        # Input('scenario-dropdown', 'value'),
        # Input('year-slider', 'value')
    )
    # def render_tab(tab, scenario, year_range):
    def render_tab(tab):
        # all_data_melted =get_data_melted(scenario, year_range)
        # all_data_melted =get_data_melted(scenario)
        if tab == 'overview':
            # register_overview_callback(app)  
            return overview_layout

        # elif tab == 'supply':
        #     # register_supply_callbacks(app)
        #     return supply_layout

        # elif tab == 'power':
        #     # register_power_callbacks(app)
        #     return power_layout

        # elif tab == 'sector':
        #     # register_sector_callbacks(app)
        #     return sector_layout

        # elif tab == 'co2':
        #     # register_emissionCO2_callback(app)
        #     return emissionCO2_layout(all_data_melted)

        # elif tab == 'search':
        #     # register_search_callbacks(app)
        #     return search_layout(all_data_melted)
        elif tab == 'all-charts':
            return all_charts_layout()
        elif tab == 'compare-scenarios':
            return compare_charts_layout()