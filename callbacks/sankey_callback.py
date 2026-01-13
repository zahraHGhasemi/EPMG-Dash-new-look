
from dash import Input, Output, State, ctx, no_update
from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
from utils.get_data import get_filtered_df
from utils.plot_chart import plot_chart
from utils.unit_handler import unit_detect, dict_unit
from dash import dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import colorsys
from data_provider.sql_data import SQLDataProvider



def prepare_sankey_data_energy_source_to_sector(scenario, year,provider = SQLDataProvider(table_name="observations")):
    df_agr = provider.get_filtered_df("AGR_FEC", scenario, [year,year])
    df_ind = provider.get_filtered_df("IND_FEC", scenario, [year,year])
    df_srv = provider.get_filtered_df("SRV_FEC", scenario, [year,year])
    df_rsd = provider.get_filtered_df("RSD_FEC", scenario, [year,year])
    df_tra = provider.get_filtered_df("TRA_FEC", scenario, [year,year])

    df_agr_filtered = df_agr[['seriesTitle', 'Value']].copy()
    df_agr_filtered['target'] = 'Agriculture'

    df_ind_filtered = df_ind[['seriesTitle', 'Value']].copy()
    df_ind_filtered['target'] = 'Industry'

    df_srv_filtered = df_srv[['seriesTitle', 'Value']].copy()
    df_srv_filtered['target'] = 'Services'

    df_rsd_filtered = df_rsd[['seriesTitle', 'Value']].copy()
    df_rsd_filtered['target'] = 'Residential'

    df_tra_filtered = df_tra[['seriesTitle', 'Value']].copy()
    df_tra_filtered['target'] = 'Transport'
    # Combine all DataFrames
    df_all = pd.concat([df_agr_filtered, df_ind_filtered, df_srv_filtered, df_rsd_filtered, df_tra_filtered], ignore_index=True) 
    return df_all
def handle_negative_elec(df_filtered):
    if not df_filtered[df_filtered['Value'] < 0].empty:
        neg_row = df_filtered[df_filtered['Value'] < 0].iloc[0]
        
        seriesTitle = neg_row['seriesTitle' ]+ ' Export'
        target = neg_row['target']
        value = -neg_row['Value']  
        df_filtered.loc[len(df_filtered)] = [target, value, seriesTitle]
        df_filtered = df_filtered.drop(neg_row.name)
    
    return df_filtered

def prepare_sankey_data_SEAI(scenario, year, provider = SQLDataProvider(table_name="observations")):
    df_SYS_TPED = provider.get_filtered_df('SYS_TPED', scenario, [year, year])
    df_FEC_Sector = provider.get_filtered_df("SYS_FEC_Sector", scenario, [year,year])
    df_renewable = provider.get_filtered_df('PWR_Gen-ELCC', scenario, [year,year])
    
    df_filtered = df_SYS_TPED[['seriesTitle','Value']]
    df_filtered.loc[len(df_filtered)] = ["Wind offshore", 0]
    df_filtered.loc[len(df_filtered)] = ["Wind onshore", 0]
    df_filtered.loc[len(df_filtered)] = ["Solar", 0]
    
    df_filtered['target'] = "Primary Energy"
    df_filtered = handle_negative_elec(df_filtered)

    if "Other renewables" in df_filtered['seriesTitle'].unique():       
        df_filtered.loc[df_filtered['seriesTitle']== "Wind offshore", 'Value'] = df_renewable[df_renewable['seriesTitle']== "Wind offshore"]['Value'].iloc[0]
       
        df_filtered.loc[df_filtered['seriesTitle']== "Wind onshore", 'Value'] = df_renewable[df_renewable['seriesTitle']== "Wind onshore"]['Value'].iloc[0]
        df_filtered.loc[df_filtered['seriesTitle']== "Solar", 'Value']= df_renewable[df_renewable['seriesTitle']== "Solar"]['Value'].iloc[0]
        sum_renewable = (df_renewable[df_renewable['seriesTitle']== "Wind offshore"]['Value'].iloc[0] + df_renewable[df_renewable['seriesTitle']== "Wind onshore"]['Value'].iloc[0] + 
                        df_renewable[df_renewable['seriesTitle']== "Solar"]['Value'].iloc[0])
        df_filtered.loc[df_filtered['seriesTitle']== "Other renewables", 'Value'] = df_filtered[df_filtered['seriesTitle']== "Other renewables"]['Value'].iloc[0] - sum_renewable
    
    new_rows = pd.DataFrame({
        'Value': df_FEC_Sector['Value'],             # Value from df_FEC_Sectore
        'seriesTitle': 'Final Energy',                # new column with constant value
        'target': df_FEC_Sector['seriesTitle']        # target column
    })

    df_filtered = pd.concat([df_filtered, new_rows], ignore_index=True)
    sum_primary = df_filtered.loc[df_filtered['target'] == "Primary Energy", 'Value'].sum()

    sum_final = df_filtered.loc[df_filtered['seriesTitle'] == "Final Energy", 'Value'].sum()
    sum_elex_export = df_filtered.loc[df_filtered['target'] == "Electricity Export", 'Value'].sum()
    loss_value = sum_primary - sum_final -sum_elex_export
    new_row = pd.DataFrame({
        'seriesTitle': ['Primary Energy', 'Primary Energy'],
        'Value': [loss_value, sum_final],
        'target': ['Loss', 'Final Energy']
    })
    df_filtered = pd.concat([df_filtered, new_row], ignore_index=True)
    sum_in = df_filtered.loc[df_filtered['seriesTitle'] == "Primary Energy", 'Value'].sum()
    sum_out = df_filtered.loc[df_filtered['target'] == "Primary Energy", 'Value'].sum()
    return df_filtered
def pastel_continuous_palette(n, s=0.35, v=0.95):
    
    colors = []
    for i in range(n):
        h = i / n                   # distribute hue 0–1
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        colors.append(f'rgb({int(r*255)}, {int(g*255)}, {int(b*255)})')
    return colors

def link_colors(df_1, df_2):
    level1 = df_1['seriesTitle'].unique().tolist()  
    level2 = df_1['target'].unique().tolist()       
    level3 = df_2['seriesTitle'].unique().tolist()  
    level4 = df_2['target'].unique().tolist()  
         
    nodes = list(dict.fromkeys(level1 + level2 + level3 + level4))
    node_indices = {name: i for i, name in enumerate(nodes)}

    n = len(nodes)
    node_colors = pastel_continuous_palette(n)
    
    return nodes, node_indices, node_colors
def compute_node_totals(df, nodes):
    # initialize
    total_in  = {node: 0 for node in nodes}
    total_out = {node: 0 for node in nodes}

    # accumulate outgoing values
    for _, row in df.iterrows():
        total_out[row['seriesTitle']] += row['Value']

    # accumulate incoming values
    for _, row in df.iterrows():
        total_in[row['target']] += row['Value']

    # final computed totals
    totals = {}

    for node in nodes:
        tin  = total_in[node]
        tout = total_out[node]

        if tin == 0:
            totals[node] = tout
        elif tout == 0:
            totals[node] = tin
        elif tin == tout or abs(tin - tout) < 1e-3:
            totals[node] = tin
        else:
            print(tin, tout)
            print('Mismatch in totals for node')
            totals[node] = -1

    return totals
def draw_sankey(df_all, year, nodes, node_indices, node_colors):
    source = df_all['seriesTitle'].map(node_indices)
    target = df_all['target'].map(node_indices)
    value  = df_all['Value']
    link_colors = [node_colors[s] for s in source]

    totals = compute_node_totals(df_all, nodes)

    # label = name + total under it
    labels = [
        f"{node}<br>{totals[node]:.1f}"
        for node in nodes
    ]
    fig = go.Figure(go.Sankey(
        node=dict(
            label=labels,
            color = node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        )
    ))
    fig.update_layout(
        title = year
    )
    return fig

def register_sankey_callback(app, provider = SQLDataProvider(table_name="observations")):
    @app.callback(
        Output('scenario-sankey-dropdown', 'options'),
        Output('scenario-sankey-dropdown', 'value'),
        Input('tabs', 'value')
    )
    def update_sankey_scenario_options(tab_value):
        scenarios = sorted(provider.get_scenarios())
        value = scenarios[0] if len(scenarios) > 0 else None
        options = [{"label": s, "value": s} for s in scenarios]

        return options, value
    @app.callback(
        Output('sankey-diagram', 'figure'),
        Output('sankey-end-diagram', 'figure'),
      
        Input('year-sankey-slider', 'value'),
        Input('scenario-sankey-dropdown', 'value'),
        Input('sankey_title_dropdown', 'value')
    )
    def update_sankey(year, scenario, title):
        if title == 0:
            df_all = prepare_sankey_data_energy_source_to_sector(scenario, year[0], provider = provider)
            df_all_end = prepare_sankey_data_energy_source_to_sector(scenario, year[1], provider = provider)

        elif title == 1:
            df_all = prepare_sankey_data_SEAI(scenario, year[0], provider = provider)
            df_all_end = prepare_sankey_data_SEAI(scenario, year[1], provider = provider)
                # Nodes
        node, node_indices, node_colors = link_colors(df_all, df_all_end)
        return draw_sankey(df_all, year[0], node, node_indices, node_colors), draw_sankey(df_all_end, year[1], node, node_indices, node_colors)
    