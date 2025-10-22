import plotly.express as px

def plot_chart(all_data_melted_filtered, type = 'area'):
    color_col = 'seriesTitle' if all_data_melted_filtered['seriesTitle'].notna().any() else 'seriesName'
    table_title = all_data_melted_filtered['tableTitle'].unique()[0] 
    title_col = table_title if  table_title != 'nan' else all_data_melted_filtered['tableName'].unique()[0] 
    if type == 'bar':
        fig = px.bar(
            all_data_melted_filtered,
            x='Year',
            y='Value', # Changed y to 'Value'
            color=color_col, #'seriesTitle', # Changed color to 'seriesName',
            title  = title_col, #all_data_melted_filtered['tableTitle'].unique()[0]
            color_discrete_sequence=px.colors.qualitative.Light24
        )
        fig.update_layout(xaxis_title='Year', yaxis_title= all_data_melted_filtered['label'].unique()[0] if not all_data_melted_filtered.empty else 'Value') # Updated yaxis_title
        return fig
    elif type == 'line':
        fig = px.line(
            all_data_melted_filtered,
            x='Year',
            y='Value', # Changed y to 'Value'
            color=color_col, #'seriesTitle', # Changed color to 'seriesName',
            title  = title_col, #tiall_data_melted_filtered['tableTitle'].unique()[0]
            color_discrete_sequence=px.colors.qualitative.Light24
        )
        fig.update_layout(xaxis_title='Year', yaxis_title= all_data_melted_filtered['label'].unique()[0] if not all_data_melted_filtered.empty else 'Value') # Updated yaxis_title
        return fig
    elif type == 'area':
        fig = px.area(
            all_data_melted_filtered,
            x='Year',
            y='Value', # Changed y to 'Value'
            color=color_col, #'seriesTitle', # Changed color to 'seriesName',
            title  = title_col, #tiall_data_melted_filtered['tableTitle'].unique()[0]
            color_discrete_sequence=px.colors.qualitative.Light24
        )
        fig.update_layout(xaxis_title='Year', yaxis_title= all_data_melted_filtered['label'].unique()[0] if not all_data_melted_filtered.empty else 'Value') # Updated yaxis_title
        return fig
def plot_pie_chart(df, year, title):
    fig = px.pie(df, values='Value', names='seriesTitle', title=f'{title} {year}', hole=0.3)

    # fig.update_layout(showlegend=False)
    
    total= int(df['Value'].sum())
    unit = df['label'].unique()[0] if not df.empty else ''
    fig.add_annotation(
        text=f"{total} {unit}",
        x=0.5, y=0.5,
        font=dict(size=15, color='black'),
        showarrow=False
    )    
    return fig
def plot_bar_chart(df, year, title):
    font_sizes = [8 + (v / max(df["Value"])) * 10 for v in df["Value"]]

    fig = px.bar(df, x='Year', y='Value', title=f'{title} {year}', color='seriesTitle',
                 color_discrete_sequence=px.colors.qualitative.Light24)
    fig.update_traces(width=0.4)  # 0.4 = relative width (0–1 scale)
    fig.update_layout(xaxis_title='Year', yaxis_title= df['label'].unique()[0] if not df.empty else 'seriesTitle')

    # fig.update_layout(showlegend=False)

    # fig.update_traces(
    #     textposition="inside",
    #     textfont= dict(color="black")  # color works well on dark bars
    # )
   

    # fig.update_layout(
    #     legend=dict(
    #         orientation="h",         # horizontal legend
    #         yanchor="top",           # anchor legend to top of its box
    #         y=-0.2,                  # move below plot area
    #         xanchor="center",        # center it horizontally
    #         x=0.5
    #     )
    # )
    return fig

from plotly.subplots import make_subplots

def plot_two_pie_charts_px(df1, year1, df2, year2, title):
    # Create the subplots layout
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=[str(year1), str(year2)]
    )

    # Create pie charts using Plotly Express
    pie1 = px.pie(df1, values='Value', names='seriesTitle', hole=0.3)
    pie2 = px.pie(df2, values='Value', names='seriesTitle', hole=0.3)

    # Add traces from px.pie to the combined figure
    for trace in pie1.data:
        fig.add_trace(trace, 1, 1)
    for trace in pie2.data:
        fig.add_trace(trace, 1, 2)

    # Add center annotations for totals
    total1 = int(df1['Value'].sum())
    total2 = int(df2['Value'].sum())
    unit1 = df1['label'].unique()[0] if not df1.empty else ''
    unit2 = df2['label'].unique()[0] if not df2.empty else ''

    fig.add_annotation(text=f"{total1} {unit1}", x=0.20, y=0.5,
                       font=dict(size=14, color='black'), showarrow=False)
    fig.add_annotation(text=f"{total2} {unit2}", x=0.80, y=0.5,
                       font=dict(size=14, color='black'), showarrow=False)

    # Update layout for shared legend
    fig.update_layout(
        title_text=title,
        legend_title_text='Series',
        legend=dict(orientation='h', y=-0.1),
        showlegend=True
    )

    return fig

def plot_two_bar_charts_px(df1, year1, df2, year2, title):
    df1 = df1.copy()
    df2 = df2.copy()
    df1["Year"] = year1
    df2["Year"] = year2
    df = px.data.tips()  # remove any old reference, just here for context
    combined_df = px.data.tips()  # placeholder
    combined_df = px.data.tips()  # delete these lines in actual use
    combined_df = df1._append(df2, ignore_index=True)

    # Optional: compute dynamic font size scaling (if you still want it)
    combined_df["font_size"] = [8 + (v / max(combined_df["Value"])) * 10 for v in combined_df["Value"]]

    # Create stacked bar chart with Plotly Express
    fig = px.bar(
        combined_df,
        x="Year",
        y="Value",
        color="seriesTitle",
        title=title,
        text="Value",
        color_discrete_sequence=px.colors.qualitative.Light24
    )

    # Update bar and layout settings
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    
    fig.update_layout(
        barmode="stack",  # stack the series for each year
        xaxis_title="Year",
        yaxis_title=combined_df['label'].unique()[0] if not combined_df.empty else 'Value',
        legend=dict(orientation='h', y=-0.1),
        legend_title_text="Series",
        bargap=0.3
    )

    return fig