
from dash import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import colorsys
from data_provider.sql_data import SQLDataProvider
from urllib.parse import urlparse, parse_qs
from auth.models import db, normalize_series_color
from utils.dashboard_settings import get_dashboard_settings
from utils.plotly_download import build_plotly_download_config

from utils.sankey_helpers import(
    primary_to_final_energy_sankey,
    prepare_detailed_sector_FEC,
    prepare_sankey_data_SEAI,
    get_sankey_title_label,
    link_colors,
    draw_sankey
)
    
session = db.session


def register_sankey_callback(app, provider = SQLDataProvider(session=session)):
    """Register Sankey dropdown and chart-rendering callbacks."""
    @app.callback(
        Output('scenario-sankey-dropdown', 'options'),
        Output('scenario-sankey-dropdown', 'value'),
        Input("url", "href"),
        State("scenario-sankey-dropdown", "value")
    )
    def update_sankey_scenario_options(href, current_value):
        """Populate Sankey scenario options from the active study in the URL."""
        if not href:
            return [], None

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return [], None

        scenarios = provider.get_scenarios_for_study(int(study_id))

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
    @app.callback(
        Output('sankey_title_dropdown', 'options'),
        Output('sankey_title_dropdown', 'value'),
        Input('year-sankey-slider', 'value'),
        Input('scenario-sankey-dropdown', 'value')
    )
    def update_sankey_title(year, scenario):
        """Populate available Sankey view options for the selected scenario."""
        if not scenario or not year:
            return [], None
        options= []
        table_name_ls_1 = ['SYS_TPED', 'SYS_FEC_Fuel', 'PWR_Gen-ELCC', "AGR_FEC", "IND_FEC", "SRV_FEC", "RSD_FEC", "TRA_FEC"]
        table_name_ls_2 = ['SYS_TPED', 'SYS_FEC_Sector', 'PWR_Gen-ELCC']
        table_name_ls_3 = provider.check_table_include_name(scenario, 'TRA', ['FuelCons'])
        table_name_ls_4 = provider.check_table_include_name(scenario, 'RSD', ['FuelCons'])
        table_name_ls_5 = provider.check_table_include_name(scenario, 'IND', ['FEC'])
        # label_1 = provider.get_labels(provider.get_table_id_by_name('SYS_TPED'))
        # label_2 = provider.get_labels(provider.get_table_id_by_name('SYS_FEC_Sector'))
        # label_3 = provider.get_labels(provider.get_table_id_by_name('TRA_FEC'))
        # label_4 = provider.get_labels(provider.get_table_id_by_name('RSD_FEC'))
        # label_5 = provider.get_labels(provider.get_table_id_by_name('IND_FEC'))
        # label_6 = provider.get_labels(provider.get_table_id_by_name('PWR_Gen-ELCC'))
        # label_7 = provider.get_labels(provider.get_table_id_by_name('AGR_FEC'))
        # label_8 = provider.get_labels(provider.get_table_id_by_name('SRV_FEC'))
        # print(label_1, label_2, label_3, label_4, label_5, label_6, label_7, label_8)


        # The first two views are only available if the core TPED and FEC tables are present.
        # However, detailed sector FEC views require their respective tables.
        # This ensures users only see options that can be rendered for their scenario.
        # If specific scenario lacks the necessary tables, the corresponding chart will not be shown.
        if len(table_name_ls_1) >0:
            options.append({'label': 'Primary Energy to Demand (PJ)', 'value': 0})
        if len(table_name_ls_2) >0:
            options.append({'label': 'Primary Energy to Final Energy (PJ)', 'value': 1})
        if len(table_name_ls_3) >0:
            options.append({'label': 'Final Energy Consumption in Transport (PJ)', 'value': 2})
        if len(table_name_ls_4) >0:
            options.append({'label': 'Final Energy Consumption in Residential (PJ)', 'value': 3})
        if len(table_name_ls_5) >0:
            options.append({'label': 'Final Energy Consumption in Industry (PJ)', 'value': 4})

        value = options[0]['value'] if options else None
        return options, value

    @app.callback(
        Output('sankey-diagram', 'figure'),
        Output('sankey-end-diagram', 'figure'),
        Output('sankey-diagram', 'config'),
        Output('sankey-end-diagram', 'config'),
      
        Input('year-sankey-slider', 'value'),
        Input('scenario-sankey-dropdown', 'value'),
        Input('sankey_title_dropdown', 'value')
    )
    def update_sankey(year, scenario, title):
        """Render start/end year Sankey diagrams and download configs for the selected view."""
        if not year or len(year) < 2:
            year = [None, None]

        title_label = get_sankey_title_label(title)
        start_config = build_plotly_download_config(
            "sankey",
            scenario,
            title_label,
            year[0],
            year[1],
            suffix=f"start_{year[0]}",
        )
        end_config = build_plotly_download_config(
            "sankey",
            scenario,
            title_label,
            year[0],
            year[1],
            suffix=f"end_{year[1]}",
        )

        if not scenario or title is None or year[0] is None or year[1] is None:
            empty_figure = go.Figure()
            return empty_figure, empty_figure, start_config, end_config

        if title == 0:
            df_all, list_table_ids = primary_to_final_energy_sankey(scenario, year[0], provider = provider)
            df_all_end, list_table_ids_end = primary_to_final_energy_sankey(scenario, year[1], provider = provider)
        elif title == 1:
            df_all, list_table_ids = prepare_sankey_data_SEAI(scenario, year[0], provider = provider)
            df_all_end, list_table_ids_end = prepare_sankey_data_SEAI(scenario, year[1], provider = provider)
        elif title == 2:
            df_all, list_table_ids = prepare_detailed_sector_FEC(scenario, year[0], 'TRA', ['FuelCons'], provider = provider)
            df_all_end, list_table_ids_end = prepare_detailed_sector_FEC(scenario, year[1], 'TRA', ['FuelCons'], provider = provider)
        elif title == 3:
            df_all, list_table_ids = prepare_detailed_sector_FEC(scenario, year[0], 'RSD', ['FuelCons'], provider = provider)
            df_all_end, list_table_ids_end = prepare_detailed_sector_FEC(scenario, year[1], 'RSD', ['FuelCons'], provider = provider)
        elif title == 4:
            df_all, list_table_ids = prepare_detailed_sector_FEC(scenario, year[0], 'IND', ['FEC'], provider = provider)
            df_all_end, list_table_ids_end = prepare_detailed_sector_FEC(scenario, year[1], 'IND', ['FEC'], provider = provider)
        
        series_color_map = provider.get_series_color_map_by_list_titles(list_table_ids + list_table_ids_end)
        node, node_indices, node_colors = link_colors(df_all, df_all_end, series_color_map)
        
        return (
            draw_sankey(
                df_all,
                year[0],
                node,
                node_indices,
                node_colors,
                scenario=scenario,
                title_label=title_label,
            ),
            draw_sankey(
                df_all_end,
                year[1],
                node,
                node_indices,
                node_colors,
                scenario=scenario,
                title_label=title_label,
            ),
            start_config,
            end_config,
        )
    
