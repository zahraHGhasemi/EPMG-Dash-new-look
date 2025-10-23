
from dash import Input, Output, State, ctx, no_update
from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
from utils.get_data import get_filtered_df
from utils.plot_chart import plot_chart
import pandas as pd
import numpy as np
import plotly.express as px
def register_compare_chart_callbacks(app):
    
    @app.callback(
        Output('compare-chart', 'figure'),
        Input('subcategory-dropdown', 'value'),
        Input('category-dropdown', 'value'),
        Input('scenario-chart-dropdown', 'value'),
        Input('year-slider', 'value'),
        Input('chart-type-dropdown', 'value'),
        Input('compare-scenario-dropdown', 'value'),
        Input('difference-radio', 'value')
        # Input('generate_btn', 'n_clicks'),
        # prevent_initial_call=True  

    )
    def update_graph(table_name,category, scenario, year_range, chart_types, compare_scenario, difference_option):
        table_id = get_table_id(table_name,category)
        df = get_filtered_df(table_id, scenario, year_range)
        df_compare = get_filtered_df(table_id, compare_scenario, year_range)

        df['source'] = 'scenario'
        df_compare['source'] = 'scenario compare'

        # Combine dataframes
        df_combined = pd.concat([df, df_compare])
        if difference_option == 'no':
            df_combined = df_combined.sort_values(by="Year")

            if chart_types == 'line':
                fig = px.line(
                    df_combined,
                    x='Year',
                    y='Value',
                    color='seriesTitle',  # separate lines by seriesName
                    facet_col='source',  # group df1 and df2 side by side
                    category_orders={'source': ['scenario', 'scenario compare']}  # different line styles for df1 and df2
                )
            elif chart_types == 'area':
                fig = px.area(
                    df_combined,
                    x='Year',
                    y='Value',
                    color='seriesTitle',  # separate areas by seriesName
                    facet_col='source',  # group df1 and df2 side by side
                    category_orders={'source': ['scenario', 'scenario compare']}                )
            else:  # Default to bar chart
                fig = px.bar(
                    df_combined,
                    x='Year',
                    y='Value',
                    color='seriesTitle',  # stacked by seriesName
                    barmode='stack',
                    facet_col='source',  # group df1 and df2 side by side
                    category_orders={'source': ['scenario', 'scenario compare']}
                )
        else:
            df = df[['tableName','Year', 'seriesTitle', 'Value', 'source']]
            df_compare = df_compare[['tableName', 'Year', 'seriesTitle', 'Value', 'source']]
            merge_cols = ['tableName', 'Year', 'seriesTitle']
            df_merged = pd.merge(df, df_compare, on=merge_cols, suffixes=('_df1','_df2'))

            df_merged = df_merged.sort_values(by="Year")
            df_merged['Difference'] = df_merged['Value_df1'] - df_merged['Value_df2']
            
            if chart_types == 'line':
                fig = px.line(
                    df_merged,
                    x='Year',
                    y='Difference',
                    color='seriesTitle',  # separate lines by seriesName
                )
            elif chart_types == 'area':
                fig = px.area(
                    df_merged,
                    x='Year',
                    y='Difference',
                    color='seriesTitle',  # separate areas by seriesName
                )
            else:  # Default to bar chart
                df_merged = df_merged.sort_values(by = "Difference")
                pos_df = df_merged[df_merged['Difference'] >= 0]
                neg_df = df_merged[df_merged['Difference'] < 0]
                unique_series = df_merged['seriesTitle'].unique()
                palette = px.colors.qualitative.Light24
                color_map = {s: palette[i % len(palette)] for i, s in enumerate(unique_series)}

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
                    title='Diverging Stacked Bar Chart (Consistent Colors)',
                    xaxis_title='Year',
                    yaxis_title='Difference',
                    template='plotly_white',
                    yaxis_zeroline=True
                )
        # fig.update_layout(title="Grouped Stacked Bar Chart")
        
        return fig
        