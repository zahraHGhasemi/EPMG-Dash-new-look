import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots



def plot_chart(all_data_melted_filtered, type = 'area', x_col = "Year", y_col = "Value", facet_col= None, category_orders = None, barmode = 'stack',color_map =[], table_title ="Selected Chart"):
    """Generic function to plot bar, line, or area charts using Plotly Express, with dynamic color mapping."""
    color_col = 'seriesTitle' if all_data_melted_filtered['seriesTitle'].notna().any() else 'seriesName'
    
    title_col = table_title
    all_data_melted_filtered = all_data_melted_filtered.sort_values(by="Year")

    if facet_col is None and 'source' in all_data_melted_filtered.columns:
        facet_col = 'source'
    if category_orders is None and facet_col:
        category_orders = {facet_col: sorted(all_data_melted_filtered[facet_col].unique())}
    if color_map ==[]:
        color_map= color_col

    if type == 'bar':
        fig = px.bar(
            all_data_melted_filtered,
            x=x_col,
            y=y_col, 
            color=color_col, 
            title  = title_col, 
            color_discrete_map= color_map,
            facet_col = facet_col,
            category_orders=category_orders
        )
        fig.update_layout(xaxis_title= x_col, yaxis_title= all_data_melted_filtered['label'].unique()[0] if not all_data_melted_filtered.empty else 'Value',
                          legend = dict(title_text='')) 
        return fig
    elif type == 'line':
        fig = px.line(
            all_data_melted_filtered,
            x=x_col,
            y=y_col, 
            color=color_col, 
            title  = title_col, 
            color_discrete_map=color_map,
            facet_col = facet_col,
            category_orders=category_orders
        )
        fig.update_layout(xaxis_title= x_col, yaxis_title= all_data_melted_filtered['label'].unique()[0] if not all_data_melted_filtered.empty else 'Value',
                          legend = dict(title_text='')) 
        return fig
    elif type == 'area':
        fig = px.area(
            all_data_melted_filtered,
            x= x_col,
            y=y_col, 
            color=color_col, 
            title  = title_col, 
            color_discrete_map=color_map,
            facet_col = facet_col,
            category_orders=category_orders
        )
        fig.update_layout(xaxis_title= x_col, yaxis_title= all_data_melted_filtered['label'].unique()[0] if not all_data_melted_filtered.empty else 'Value', 
                          legend = dict(title_text=''))  
        return fig
    

# def plot_pie_chart(df, year, title, color_map=None):
#     """Function to plot a pie chart using Plotly Express, with dynamic color mapping and center annotation for total value for the overview tab."""
#     fig = px.pie(
#         df,
#         values='Value',
#         names='seriesTitle',
#         title=f'{title} {year}',
#         hole=0.3,
#         color='seriesTitle',
#         color_discrete_map=color_map,
#     )

    
#     total= int(df['Value'].sum())
#     unit = df['label'].unique()[0] if not df.empty else ''
#     fig.add_annotation(
#         text=f"{total} {unit}",
#         x=0.5, y=0.5,
#         font=dict(size=15, color='black'),
#         showarrow=False
#     )    
#     return fig

# def plot_bar_chart(df, year, title):
#     font_sizes = [8 + (v / max(df["Value"])) * 10 for v in df["Value"]]

#     fig = px.bar(df, x='Year', y='Value', title=f'{title} {year}', color='seriesTitle',
#                  color_discrete_sequence=px.colors.qualitative.Light24)
#     fig.update_traces(width=0.4)  
#     fig.update_layout(xaxis_title='Year', yaxis_title= df['label'].unique()[0] if not df.empty else 'seriesTitle')

#     return fig


def plot_two_pie_charts_px(df1, year1, df2, year2, title, label='Value', color_map=None):
    """Function to plot two pie charts side by side using Plotly Express, with dynamic color mapping and center annotations for total values for the overview tab."""
    # Create the subplots layout
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=[str(year1), str(year2)]
    )

    # Create pie charts using Plotly Express
    pie1 = px.pie(
        df1,
        values='Value',
        names='seriesTitle',
        hole=0.3,
        color='seriesTitle',
        color_discrete_map=color_map,
    )
    pie2 = px.pie(
        df2,
        values='Value',
        names='seriesTitle',
        hole=0.3,
        color='seriesTitle',
        color_discrete_map=color_map,
    )

    for trace in pie1.data:
        trace.textposition='inside'
        trace.textinfo='percent+label'
        
        fig.add_trace(trace, 1, 1)

    for trace in pie2.data:
        trace.textposition='inside'
        trace.textinfo='percent+label'
       
        fig.add_trace(trace, 1, 2)

    # Add center annotations for totals
    total1 = int(df1['Value'].sum())
    total2 = int(df2['Value'].sum())
    unit1 = label
    unit2 = label

    fig.add_annotation(text=f"{total1} {unit1}", x=0.20, y=0.5,
                       font=dict(size=14, color='black'), showarrow=False)
    fig.add_annotation(text=f"{total2} {unit2}", x=0.80, y=0.5,
                       font=dict(size=14, color='black'), showarrow=False)

    # Update layout for title and legend
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=18)
        ),
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.1,
            yanchor='top',
            itemclick=False,        # disables single-click toggling
            itemdoubleclick=False
        )
    )

    return fig

def plot_two_bar_charts_px(df1, year1, df2, year2, title, label, color_map=None):
    """Function to plot two bar charts side by side using Plotly Express, with dynamic color mapping for the overview tab."""
    df1 = df1.copy()
    df2 = df2.copy()
    df1["Year"] = year1
    df2["Year"] = year2
   
    combined_df = pd.concat([df1, df2], ignore_index=True)
    
    combined_df["font_size"] = [8 + (v / max(combined_df["Value"])) * 10 for v in combined_df["Value"]]

    # Create stacked bar chart with Plotly Express
    fig = px.bar(
        combined_df,
        x="Year",
        y="Value",
        color="seriesTitle",
        title=title,
        text="Value",
        color_discrete_map=color_map,
    )

    # Update bar and layout settings
      
    fig.update_traces(
        texttemplate='%{text:.2s}',
        textposition='inside',      # place numbers inside each segment
        insidetextanchor='start',   # align text to the start (left) of the segment
        width=2
    ) 
    fig.update_layout(
        barmode="stack",
        xaxis_title="Year",
        yaxis_title=label,
        bargap=0.5,  # spacing between bars, bigger = thinner
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=18)
        ),
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.2,
            yanchor='top',
            title_text='',
            itemclick=False,        # disables single-click toggling
            itemdoubleclick=False
        )
    )

    return fig
