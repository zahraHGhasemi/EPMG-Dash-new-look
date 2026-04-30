
from dash import Input, Output, ALL, State
from utils.plot_chart import plot_chart
from utils.unit_handler import unit_detect, dict_unit
import pandas as pd
import plotly.express as px
from dash import html, dcc
import dash_bootstrap_components as dbc
from data_provider.sql_data import SQLDataProvider
from auth.models import Study, normalize_series_color, pastel_continuous_palette

from auth.models import db
from urllib.parse import urlparse, parse_qs
from utils.plotly_download import build_plotly_download_config
session = db.session
def register_compare_chart_callbacks(app, provider = SQLDataProvider(session=session)):
    """Register callbacks for scenario comparison charts, colors, and CSV downloads."""
    @app.callback(
        Output('compare-scenario-dropdown', 'options'),
        Output('compare-scenario-dropdown', 'value'),
        Input("url", "href"),
        State("compare-scenario-dropdown", "value")
    )
    def update_scenario_dropdown(href, current_value):
        """Populate comparison scenario options from the active study in the URL."""
        if not href:
            return [], None

        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        if not study_id:
            return [], None

        try:
            scenarios = provider.get_scenarios_for_study(int(study_id))
        except (TypeError, ValueError):
            return [], None

        options = [{"label": s.name, "value": s.name} for s in scenarios]
        option_values = {opt["value"] for opt in options}
        if current_value in option_values:
            value = current_value
        else:
            value = options[1]["value"] if len(options) > 1 else None
        return options, value
    
    @app.callback(
        Output('color-accordion', 'children'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value')
    )
    def update_color_accordion(table_name,category, scenario, year_range):
        """Build color-picker controls for the selected table's series."""
        
        table_id = provider.get_table_id(table_name, category)
        
        series_rows = provider.get_series_titles_with_colors(table_id)
        fallback_palette = pastel_continuous_palette(len(series_rows))
        default_colors = []
        for i, row in enumerate(series_rows):
            color = normalize_series_color(row["color"])
            if not color:
                color = fallback_palette[i]
            default_colors.append(color)

        children_colors = []
        for i, row in enumerate(series_rows):
            children_colors.append(html.Div([
                    html.Label(f"{row['title']}"),
                dbc.Input(
                        id={'type': 'series-color-input', 'index': row["id"]},
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
        Output('compare-chart', 'config'),
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
        """Render the chart, optional comparison view, or scenario difference view."""
        year_start, year_end = (year_range or [None, None])[:2]
        suffix = None
        if compare_value and compare_scenario:
            suffix = f"vs_{compare_scenario}"
            if difference_option == 'yes':
                suffix = f"{suffix}_difference"

        config = build_plotly_download_config(
            "charts",
            scenario,
            table_name,
            year_start,
            year_end,
            suffix=suffix,
        )

        table_id = provider.get_table_id(table_name, category)
        df = provider.get_filtered_df(table_id, scenario, year_range)
        series_rows = provider.get_series_titles_with_colors(table_id)
        color_map = {
            row["title"]: color_values[i]
            for i, row in enumerate(series_rows[:len(color_values)])
        }
        df['label'] = unit
        if unit in dict_unit.keys():
                df = unit_detect( unit, df)
        if compare_value:
            df_compare = provider.get_filtered_df(table_id, compare_scenario, year_range)
            

            df['source'] = 'scenario'
            df_compare['source'] = 'scenario compare'
            df_compare['label'] = unit
            if unit in dict_unit.keys():
                df_compare = unit_detect(unit, df_compare)

            df_combined = pd.concat([df, df_compare])
            


            if difference_option == 'no':
                df_combined = df_combined.sort_values(by="Year")
                
                fig = plot_chart(df_combined, chart_types, facet_col = 'source',category_orders={'source': ['scenario', 'scenario compare']}, color_map=color_map, table_title=table_name)

            else:
                
                merge_cols = [ 'Year', 'seriesTitle']
                df_merged = pd.merge(df, df_compare, on=merge_cols, suffixes=('_df1','_df2'))
                df_merged = df_merged.sort_values(by="Year")
                df_merged['Difference'] = df_merged['Value_df1'] - df_merged['Value_df2']
                df_merged['Value'] = df_merged['Difference']
                df_merged['label'] = unit
                if chart_types == 'bar':  # Default to bar chart
                    df_merged = df_merged.sort_values(by = "Difference")
                    pos_df = df_merged[df_merged['Difference'] >= 0]
                    neg_df = df_merged[df_merged['Difference'] < 0]
                   
                    fig = px.bar(
                        pos_df,
                        x='Year',
                        y='Difference',
                        color='seriesTitle',
                        color_discrete_map=color_map
                    )

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
                    
                else:
                    fig = plot_chart(df_merged, chart_types, color_map= color_map, y_col='Difference',table_title=table_name)
            return fig, config
        else:
            
            return plot_chart(df, chart_types, color_map= color_map, table_title=table_name), config
    @app.callback(
        Output("download-dataframe-csv", "data"),
        Input("btn-download", "n_clicks"),
        State('subcategory-dropdown', 'value'),
        State('category-dropdown', 'value'),
        State('scenario-chart-dropdown', 'value'),
        State('year-slider', 'value'),
        State('url', "href"),
        State('unit-dropdown', "value"),
        prevent_initial_call=True
    )
    def download_current_chart(n_clicks, table_name,category, scenario, year_range, href, unit):
        """Export the currently selected chart data as a CSV file."""
        
        query = parse_qs(urlparse(href).query)
        study_id = query.get("study_id", [None])[0]

        # Read study name from study_id
        study_name = "Unknown Study"
        if study_id is not None:
            study = Study.query.get(study_id)   # adjust based on your ORM/model
            if study:
                study_name = study.name
        
        table_id = provider.get_table_id(table_name, category)
        df = provider.get_filtered_df(table_id, scenario, year_range)
        df = unit_detect(unit, df) if unit in dict_unit.keys() else df
        df['label'] = unit
        df['study'] = study_name
        df['tableName'] = table_name
        return dcc.send_data_frame(df.to_csv, f"{table_name}_{scenario}_{year_range[0]}-{year_range[1]}_{study_name}.csv", index=False)
            
