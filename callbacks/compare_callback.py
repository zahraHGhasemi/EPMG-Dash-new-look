
from dash import Input, Output, ALL, State
# from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
# from utils.get_data import get_filtered_df, get_user_df
from utils.plot_chart import plot_chart
from utils.unit_handler import unit_detect, dict_unit
import pandas as pd
import numpy as np
import plotly.express as px
from dash import html, dcc
import dash_bootstrap_components as dbc
import colorsys
from flask import has_request_context
from data_provider.sql_data import SQLDataProvider
from data_provider.dataframe_data import DataFrameProvider

def pastel_continuous_palette(n, s=0.35, v=0.95):
    colors = []
    for i in range(n):
        h = i / n
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        hex_color = f'#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}'
        colors.append(hex_color)
    return colors
from auth.models import db
from urllib.parse import urlparse, parse_qs
session = db.session
def register_compare_chart_callbacks(app, provider = SQLDataProvider(session=session)):
    @app.callback(
        Output('compare-scenario-dropdown', 'options'),
        Output('compare-scenario-dropdown', 'value'),
        # Input('tabs', 'value')  # just a dummy input to trigger on load
        Input("url", "href")
    )
    def update_scenario_dropdown(href):
        if not href:
            return []

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return []

        scenarios = provider.get_scenarios_for_study(int(study_id))
        options = [{"label": s.name, "value": s.name} for s in scenarios]
        value = options[1]["value"] if len(options) > 1 else None
        return options, value
    # def update_compare_scenarios(tab_value):
    #     scenarios = sorted(provider.get_scenarios())
    #     value = scenarios[1] if len(scenarios) > 1 else None
    #     options = [{"label": s, "value": s} for s in scenarios]

    #     return options, value
    @app.callback(
        Output('color-accordion', 'children'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value')
    )
    def update_color_accordion(table_name,category, scenario, year_range):
        # df_user = None
        # if data_mode == "user" and has_request_context():
        #     df_user = get_user_df()
        
        # table_id = get_table_id(table_name,category, df_override=df_user)
        # df = get_filtered_df(table_id, scenario, year_range, df_override=df_user)
        table_id = provider.get_table_id(table_name, category)
        # df = provider.get_filtered_df(table_id, scenario, year_range)

        # series = df['seriesTitle'].unique().
        series = provider.get_series_titles(table_id)
        default_colors = pastel_continuous_palette(len(series))

        children_colors = []
        for i, s in enumerate(series):
            children_colors.append(html.Div([
                    html.Label(f"{s}"),
                    dbc.Input(
                        id={'type': 'series-color-input', 'index': s},
                        type='color',
                        value=default_colors[i % len(default_colors)],
                        style={'width': '60px', 'margin-right': '10px'}
                    )
                ], style={
                    "display": "inline-flex",
                    "align-items": "center",
                    "margin-right": "20px",
                    "margin-bottom": "10px",
                })
            )
        return children_colors
            
    @app.callback(
        Output('compare-chart', 'figure'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value'),
        Input('chart-type-dropdown', 'value'),
        Input('compare-scenario-dropdown', 'value'),
        Input('difference-radio', 'value'),
        Input('unit-dropdown', "value"),
        Input('compare-radio', 'value'),
        Input({'type': 'series-color-input', 'index': ALL}, 'value')

    )
    def update_graph(table_name,category, scenario, year_range, chart_types, compare_scenario, difference_option, unit,compare_value, color_values):
        # df_user = None
        # if data_mode == "user" and has_request_context():
        #     df_user = get_user_df()
        # table_id = get_table_id(table_name,category, df_override=df_user)
        # df = get_filtered_df(table_id, scenario, year_range, df_override=df_user)
        table_id = provider.get_table_id(table_name, category)
        df = provider.get_filtered_df(table_id, scenario, year_range)
        series_names = provider.get_series_titles(table_id)
        color_map = {series_names[i]: color_values[i] for i in range(len(series_names))}
        df['label'] = unit
        if compare_value:
            # df_compare = get_filtered_df(table_id, compare_scenario, year_range, df_override=df_user)
            df_compare = provider.get_filtered_df(table_id, compare_scenario, year_range)
            
            if unit in dict_unit.keys():
                df = unit_detect(unit, df)
                df_compare = unit_detect(unit, df_compare)

            df['source'] = 'scenario'
            df_compare['source'] = 'scenario compare'
            df_compare['label'] = unit
            # Combine dataframes
            df_combined = pd.concat([df, df_compare])
            if difference_option == 'no':
                df_combined = df_combined.sort_values(by="Year")
                fig = plot_chart(df_combined, chart_types, facet_col = 'source',category_orders={'source': ['scenario', 'scenario compare']}, color_map=color_map, table_title=table_name)

            else:
                
                # df = df[['tableName','Year', 'seriesTitle', 'Value', 'source', 'tableTitle',  'label']]
                # df_compare = df_compare[['tableName', 'Year', 'seriesTitle', 'Value', 'source', 'tableTitle',  'label']]
            
                # merge_cols = ['tableName', 'Year', 'seriesTitle', 'tableTitle',  'label']
                # df_merged = pd.merge(df, df_compare, on=merge_cols, suffixes=('_df1','_df2'))
                
                merge_cols = [ 'Year', 'seriesTitle']
                df_merged = pd.merge(df, df_compare, on=merge_cols, suffixes=('_df1','_df2'))
                df_merged = df_merged.sort_values(by="Year")
                df_merged['Difference'] = df_merged['Value_df1'] - df_merged['Value_df2']
                
                if chart_types == 'bar':  # Default to bar chart
                    df_merged = df_merged.sort_values(by = "Difference")
                    pos_df = df_merged[df_merged['Difference'] >= 0]
                    neg_df = df_merged[df_merged['Difference'] < 0]

                    # unique_series = df_merged['seriesTitle'].unique()
                    # palette = px.colors.qualitative.Light24
                    # color_map = {s: palette[i % len(palette)] for i, s in enumerate(unique_series)}

                    # --- Positive figure ---
                    fig = px.bar(
                        pos_df,
                        x='Year',
                        y='Difference',
                        color='seriesTitle',
                        color_discrete_map=color_map
                    )

                    # --- Negative figure ---
                    fig_neg = px.bar(
                        neg_df,
                        x='Year',
                        y='Difference',
                        color='seriesTitle',
                        color_discrete_map=color_map
                    )

                    # Merge both sets of traces
                    existing_legends = set(trace.name for trace in fig.data)
                    for trace in fig_neg.data:
                        if trace.name in existing_legends:
                            trace.showlegend = False  # hide duplicates in legend
                        fig.add_trace(trace)

                    # Update layout
                    fig.update_layout(
                        barmode='relative',  # positive up, negative down
                        title='Stacked Bar Chart',
                        xaxis_title='Year',
                        yaxis_title='Difference',
                        template='plotly_white',
                        yaxis_zeroline=True,
                        legend = dict(title_text='')
                    )
                    
            # fig.update_layout(title="Grouped Stacked Bar Chart")
                else:
                    fig = plot_chart(df_merged, chart_types, color_map= color_map, y_col='Difference',table_title=table_name)
            return fig
        else:
            if unit in dict_unit.keys():
                df = unit_detect( unit, df)
            return plot_chart(df, chart_types, color_map= color_map, table_title=table_name)
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
        df_override = None
        # if data_mode == "user" and has_request_context():
        #     df_override = get_user_df()
        
        # table_id = get_table_id(table_name,category, df_override=df_override)
        # df = get_filtered_df(table_id, scenario, year_range, df_override=df_override)
        table_id = provider.get_table_id(table_name, category)
        df = provider.get_filtered_df(table_id, scenario, year_range)

        return dcc.send_data_frame(df.to_csv, f"chart_data_{year_range}.csv", index=False)
            




# def register_compare_chart_callbacks(app):
#     @app.callback(
#         Output('color-accordion', 'children'),
#         Input('subcategory-dropdown', 'value'),
#         Input('category-dropdown', 'value'),
#         Input('scenario-chart-dropdown', 'value'),
#         Input('year-slider', 'value')
#     )
#     def update_color_accordion(table_name,category, scenario, year_range):
#         default_colors = px.colors.qualitative.Light24
#         table_id = get_table_id(table_name,category)
#         df = get_filtered_df(table_id, scenario, year_range)
#         print(df['seriesTitle'].unique())

#         series = df['seriesTitle'].unique()
#         children_colors = []
#         for i, s in enumerate(series):
#             children_colors.append(html.Div([
#                     html.Label(f"{s}"),
#                     dbc.Input(
#                         id={'type': 'series-color-input', 'index': s},
#                         type='color',
#                         value=default_colors[i % len(default_colors)],
#                         style={'width': '60px', 'margin-right': '10px'}
#                     )
#                 ], style={'margin-bottom': '5px'}))
#         return children_colors
            
#     @app.callback(
#         Output('compare-chart', 'figure'),
#         Input('subcategory-dropdown', 'value'),
#         Input('category-dropdown', 'value'),
#         Input('scenario-chart-dropdown', 'value'),
#         Input('year-slider', 'value'),
#         Input('chart-type-dropdown', 'value'),
#         Input('compare-scenario-dropdown', 'value'),
#         Input('difference-radio', 'value'),
#         Input('unit-dropdown', "value"),
#         Input('compare-radio', 'value')

#     )
#     def update_graph(table_name,category, scenario, year_range, chart_types, compare_scenario, difference_option, unit,compare_value):
#         table_id = get_table_id(table_name,category)
#         df = get_filtered_df(table_id, scenario, year_range)
        
#         if compare_value:
#             df_compare = get_filtered_df(table_id, compare_scenario, year_range)

#             if unit in dict_unit.keys():
#                 df = unit_detect(unit, df)
#                 df_compare = unit_detect(unit, df_compare)

#             df['source'] = 'scenario'
#             df_compare['source'] = 'scenario compare'

#             # Combine dataframes
#             df_combined = pd.concat([df, df_compare])
#             if difference_option == 'no':
#                 df_combined = df_combined.sort_values(by="Year")
#                 fig = plot_chart(df_combined, chart_types, facet_col = 'source',category_orders={'source': ['scenario', 'scenario compare']})

#             else:
                
#                 df = df[['tableName','Year', 'seriesTitle', 'Value', 'source', 'tableTitle',  'label']]
#                 df_compare = df_compare[['tableName', 'Year', 'seriesTitle', 'Value', 'source', 'tableTitle',  'label']]
            
#                 merge_cols = ['tableName', 'Year', 'seriesTitle', 'tableTitle',  'label']
#                 df_merged = pd.merge(df, df_compare, on=merge_cols, suffixes=('_df1','_df2'))

#                 df_merged = df_merged.sort_values(by="Year")
#                 df_merged['Difference'] = df_merged['Value_df1'] - df_merged['Value_df2']
                
#                 if chart_types == 'bar':  # Default to bar chart
#                     df_merged = df_merged.sort_values(by = "Difference")
#                     pos_df = df_merged[df_merged['Difference'] >= 0]
#                     neg_df = df_merged[df_merged['Difference'] < 0]
#                     unique_series = df_merged['seriesTitle'].unique()
#                     palette = px.colors.qualitative.Light24
#                     color_map = {s: palette[i % len(palette)] for i, s in enumerate(unique_series)}

#                     # --- Positive figure ---
#                     fig = px.bar(
#                         pos_df,
#                         x='Year',
#                         y='Difference',
#                         color='seriesTitle',
#                         color_discrete_map=color_map
#                     )

#                     # --- Negative figure ---
#                     fig_neg = px.bar(
#                         neg_df,
#                         x='Year',
#                         y='Difference',
#                         color='seriesTitle',
#                         color_discrete_map=color_map
#                     )

#                     # Merge both sets of traces
#                     existing_legends = set(trace.name for trace in fig.data)
#                     for trace in fig_neg.data:
#                         if trace.name in existing_legends:
#                             trace.showlegend = False  # hide duplicates in legend
#                         fig.add_trace(trace)

#                     # Update layout
#                     fig.update_layout(
#                         barmode='relative',  # positive up, negative down
#                         title='Stacked Bar Chart',
#                         xaxis_title='Year',
#                         yaxis_title='Difference',
#                         template='plotly_white',
#                         yaxis_zeroline=True,
#                         legend = dict(title_text='')
#                     )
                    
#             # fig.update_layout(title="Grouped Stacked Bar Chart")
#                 else:
#                     fig = plot_chart(df_merged, chart_types, y_col='Difference')
#             return fig
#         else:
#             if unit in dict_unit.keys():
#                 df = unit_detect( unit, df)
#             return plot_chart(df, chart_types)
            