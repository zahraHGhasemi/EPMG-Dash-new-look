
from dash import Input, Output, State, ctx, no_update
from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
from utils.get_data import get_filtered_df
from utils.plot_chart import plot_chart
from utils.unit_handler import unit_detect, dict_unit
from dash import dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
def register_sankey_callback(app):
    @app.callback(
        Output('sankey-diagram', 'figure'),
        Input('year-sankey-dropdown', 'value'),
        Input('scenario-sankey-dropdown', 'value')
    )
    def update_sankey(year, scenario):
        # df_SYS_TPED = get_filtered_df('SYS_TPED', scenario, [year, year])
        # df_FEC_Sector = get_filtered_df("SYS_FEC_Sector", scenario, [year,year])
        # df_renewable = get_filtered_df('PWR_Gen-ELCC', scenario, [year,year])
        
        # print(df_SYS_TPED['seriesTitle'].unique(), "df_SYS_TPED['seriesTitle'].unique()")
        # print(df_FEC_Sector['seriesTitle'].unique(), "df_FEC_Sector['seriesTitle'].unique()")
        # print(df_renewable['seriesTitle'].unique(), "df_renewable['seriesTitle'].unique()")

        # df_filtered = df_SYS_TPED['seriesTitle']

        df_agr = get_filtered_df("AGR_FEC", scenario, [year,year])
        df_ind = get_filtered_df("IND_FEC", scenario, [year,year])
        df_srv = get_filtered_df("SRV_FEC", scenario, [year,year])
        df_rsd = get_filtered_df("RSD_FEC", scenario, [year,year])
        df_tra = get_filtered_df("TRA_FEC", scenario, [year,year])

        df_agr_filtered = df_agr[['seriesTitle', 'Value']].copy()
        df_agr_filtered['sector'] = 'Agriculture'

        df_ind_filtered = df_ind[['seriesTitle', 'Value']].copy()
        df_ind_filtered['sector'] = 'Industry'

        df_srv_filtered = df_srv[['seriesTitle', 'Value']].copy()
        df_srv_filtered['sector'] = 'Services'

        df_rsd_filtered = df_rsd[['seriesTitle', 'Value']].copy()
        df_rsd_filtered['sector'] = 'Residential'

        df_tra_filtered = df_tra[['seriesTitle', 'Value']].copy()
        df_tra_filtered['sector'] = 'Transport'
        # Combine all DataFrames
        df_all = pd.concat([df_agr_filtered, df_ind_filtered, df_srv_filtered, df_rsd_filtered, df_tra_filtered], ignore_index=True)     

                # Nodes
        level1 = df_all['seriesTitle'].unique().tolist()  # energy sources
        level2 = df_all['sector'].unique().tolist()       # sectors
        nodes = level1 + level2
        node_indices = {name: i for i, name in enumerate(nodes)}

        # Links
        source = df_all['seriesTitle'].map(node_indices)
        target = df_all['sector'].map(node_indices)
        value  = df_all['Value']

        df_links = pd.DataFrame({
            "source": df_all['seriesTitle'],
            "target": df_all['sector'],
            "value": df_all['Value']
        })

        fig = go.Figure(go.Sankey(
            node=dict(
                label=nodes
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            )
        ))

        fig.update_layout(title_text="Energy Sources → Sectors", font_size=12)
        return fig
    