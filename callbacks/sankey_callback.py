
from dash import Input, Output, State, ctx, no_update
# from utils.get_data import get_categories, get_subcategories, get_table_id, get_subcategory_name
# from utils.get_data import get_filtered_df
# from utils.plot_chart import plot_chart
# from utils.unit_handler import unit_detect, dict_unit
from dash import dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import colorsys
from data_provider.sql_data import SQLDataProvider
from urllib.parse import urlparse, parse_qs
from auth.models import db, normalize_series_color
from utils.dashboard_settings import get_dashboard_settings
from utils.plotly_download import build_plotly_download_config

session = db.session
OIL = 'Oil'
NATURAL_GAS = 'Natural gas'
BIOENERGY = 'Bioenergy'
OTHER_RENEWABLES = 'Other renewables'
COAL = 'Coal'
PEAT = 'Peat'
HYDROGEN = 'Hydrogen'
SOLAR = 'Solar'
WIND_ONSHORE = 'Wind onshore'
WIND_OFFSHORE = 'Wind offshore'
ELECTRICITY_GENERATION = 'Electricity supply'
ELECTRICITY_LOSS = 'Electricity loss'
ELECTRICITY_IMPORT = 'Electricity import'
ELECTRICITY_EXPORT = 'Electricity export'
LOSS = 'Loss'
RSD = 'Residential'
IND = 'Industry'
SRV = 'Services'
AGR = 'Agriculture'
TRA = 'Transport'
GAS_TO_ELEC_EFFICIENCY = 0.6
HYDROGEN_TO_ELEC_EFFICIENCY = 0.59
BIOENERGY_TO_ELEC_EFFICIENCY = 0.35
GRID_EFFICIENCY = 0.94
ELECTRICITY_TO_H2_EFFICIENCY = 0.85



def prepare_elec_gen_data(df_PWR_Gen_ELCC):
    df_PWR_Gen_ELCC_filtered = df_PWR_Gen_ELCC[['seriesName', 'Value', 'seriesTitle']].copy()
    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('GAS'), 'seriesTitle'] = NATURAL_GAS

    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('BIO'), 'seriesTitle'] = BIOENERGY

    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('PWR-MSW'), 'seriesTitle'] = OTHER_RENEWABLES
    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('PWR-OCE'), 'seriesTitle'] = OTHER_RENEWABLES
    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('PWR-HYD'), 'seriesTitle'] = OTHER_RENEWABLES
    df_PWR_Gen_ELCC_filtered['target'] = ELECTRICITY_GENERATION
    
    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('H2'), 'Value'] /= HYDROGEN_TO_ELEC_EFFICIENCY
    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('GAS'), 'Value'] /= GAS_TO_ELEC_EFFICIENCY
    df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('BIO'), 'Value'] /= BIOENERGY_TO_ELEC_EFFICIENCY
    if df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('H2'), 'Value'].sum() > 0: 
        new_row = pd.DataFrame({
            'seriesName': [ELECTRICITY_GENERATION],
            'Value': [df_PWR_Gen_ELCC_filtered.loc[df_PWR_Gen_ELCC_filtered['seriesName'].str.contains('H2'), 'Value'].sum()/ELECTRICITY_TO_H2_EFFICIENCY],
            'seriesTitle': [ELECTRICITY_GENERATION],
            'target': [HYDROGEN]
        })

        df_PWR_Gen_ELCC_filtered = pd.concat([df_PWR_Gen_ELCC_filtered, new_row], ignore_index=True)
    return df_PWR_Gen_ELCC_filtered[['seriesTitle', 'Value', 'target']]

def prepare_residential_data(df_rsd):
    df_rsd_filtered = df_rsd[['seriesTitle', 'Value', 'seriesName']].copy()
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDKER'), 'seriesTitle'] = OIL
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDGAS'), 'seriesTitle'] = NATURAL_GAS
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDLPG'), 'seriesTitle'] = NATURAL_GAS
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDWOO'), 'seriesTitle'] = BIOENERGY
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDBDL'), 'seriesTitle'] = BIOENERGY
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDBGS'), 'seriesTitle'] = BIOENERGY
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDETH'), 'seriesTitle'] = BIOENERGY
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDAHT'), 'seriesTitle'] = OTHER_RENEWABLES
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDHET'), 'seriesTitle'] = OTHER_RENEWABLES
    df_rsd_filtered.loc[df_rsd_filtered['seriesName'].str.contains('RSDELC'), 'seriesTitle'] = ELECTRICITY_GENERATION

    df_rsd_filtered['target'] = RSD
    return df_rsd_filtered[['seriesTitle', 'Value', 'target']]

def prepare_transport_data(df_tra):
    df_tra_filtered = df_tra[['seriesTitle', 'Value', 'seriesName']].copy()
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('DST'), 'seriesTitle'] = OIL
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('GSL'), 'seriesTitle'] = OIL
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('KER'), 'seriesTitle'] = OIL
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('CNG'), 'seriesTitle'] = NATURAL_GAS
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('LNG'), 'seriesTitle'] = NATURAL_GAS
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('BDL'), 'seriesTitle'] = BIOENERGY
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('ETH'), 'seriesTitle'] = BIOENERGY
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('BNG'), 'seriesTitle'] = BIOENERGY
    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('BJK'), 'seriesTitle'] = BIOENERGY

    df_tra_filtered.loc[df_tra_filtered['seriesName'].str.contains('ELC'), 'seriesTitle'] = ELECTRICITY_GENERATION

    df_tra_filtered['target'] = TRA
    return df_tra_filtered[['seriesTitle', 'Value', 'target']]

def prepare_industry_data(df_ind):
    df_ind_filtered = df_ind[['seriesTitle', 'Value', 'seriesName']].copy()
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDBIO'), 'seriesTitle'] = BIOENERGY
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDBGS'), 'seriesTitle'] = BIOENERGY
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDWOO'), 'seriesTitle'] = BIOENERGY
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDCOK'), 'seriesTitle'] = COAL
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDNWS'), 'seriesTitle'] = OTHER_RENEWABLES
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDRWS'), 'seriesTitle'] = OTHER_RENEWABLES
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDOIL'), 'seriesTitle'] = OIL
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('INDH2'), 'seriesTitle'] = HYDROGEN
    df_ind_filtered.loc[df_ind_filtered['seriesName'].str.contains('ELC'), 'seriesTitle'] = ELECTRICITY_GENERATION

    df_ind_filtered['target'] = IND
    return df_ind_filtered[['seriesTitle', 'Value', 'target']]

def prepare_agriculture_data(df_agr):
    df_agr_filtered = df_agr[['seriesTitle', 'Value', 'seriesName']].copy()
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('AGRDST'), 'seriesTitle'] = OIL
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('GAS'), 'seriesTitle'] = NATURAL_GAS
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('LPG'), 'seriesTitle'] = NATURAL_GAS
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('AGRBDL'), 'seriesTitle'] = BIOENERGY
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('AGRBIO'), 'seriesTitle'] = BIOENERGY
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('AGRBGS'), 'seriesTitle'] = BIOENERGY
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('AGRGEO'), 'seriesTitle'] = OTHER_RENEWABLES
    df_agr_filtered.loc[df_agr_filtered['seriesName'].str.contains('ELC'), 'seriesTitle'] = ELECTRICITY_GENERATION

    df_agr_filtered['target'] = AGR
    return df_agr_filtered[['seriesTitle', 'Value', 'target']]

def prepare_service_data(df_srv):
    df_srv_filtered = df_srv[['seriesTitle', 'Value', 'seriesName']].copy()
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('SRVGAS'), 'seriesTitle'] = NATURAL_GAS
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('SRVLPG'), 'seriesTitle'] = NATURAL_GAS
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('SRVBIO'), 'seriesTitle'] = BIOENERGY
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('SRVBGS'), 'seriesTitle'] = BIOENERGY
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('SRVAHT'), 'seriesTitle'] = OTHER_RENEWABLES
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('SRVHET'), 'seriesTitle'] = OTHER_RENEWABLES
  
    df_srv_filtered.loc[df_srv_filtered['seriesName'].str.contains('ELC'), 'seriesTitle'] = ELECTRICITY_GENERATION

    df_srv_filtered['target'] = SRV
    return df_srv_filtered[['seriesTitle', 'Value', 'target']]
def energy_loss_calculation(df, df_SYS_TPED):
    ls_feul = df['seriesTitle'].unique().tolist()
    df_SYS_TPED['target'] = LOSS
    if df_SYS_TPED[df_SYS_TPED['seriesTitle'].str.contains('Electricity')]['Value'].sum() >=0:
        df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'].str.contains('Electricity'), 'seriesTitle'] = ELECTRICITY_IMPORT
        df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'].str.contains(ELECTRICITY_IMPORT), 'target'] = ELECTRICITY_GENERATION
    else:
        df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'].str.contains('Electricity'), 'Value'] = -1 *df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'].str.contains('Electricity'), 'Value']
        df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'].str.contains('Electricity'), 'target'] = ELECTRICITY_EXPORT
        df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'].str.contains('Electricity'), 'seriesTitle'] = ELECTRICITY_GENERATION
    
    total_demand_exclude_elec = 0
    total_cons_exclude_elec = 0
    
    for i in ls_feul:
        if i == ELECTRICITY_GENERATION:
            continue
        total_demand_exclude_elec +=  df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'] == i, 'Value'].sum()
        total_cons_exclude_elec +=  df[df['seriesTitle'] == i]['Value'].sum()
        df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'] == i, 'Value'] -= df[df['seriesTitle'] == i]['Value'].sum()
        if i == OTHER_RENEWABLES:
            df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'] == i, 'Value'] -= df[df['seriesTitle'] == SOLAR]['Value'].sum()
            df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'] == i, 'Value'] -= df[df['seriesTitle'] == WIND_ONSHORE]['Value'].sum()
            df_SYS_TPED.loc[df_SYS_TPED['seriesTitle'] == i, 'Value'] -= df[df['seriesTitle'] == WIND_OFFSHORE]['Value'].sum()
    # print( total_demand_exclude_elec, 'total_demand_exclude_elec',total_cons_exclude_elec,'total_cons_exclude_elec************')
   
    return df_SYS_TPED[['seriesTitle', 'Value', 'target']]

def primary_to_final_energy_sankey(scenario, year, provider = SQLDataProvider(session=session)):
    table_id_SYS_TPED = provider.get_table_id_by_name('SYS_TPED')
    df_SYS_TPED = provider.get_filtered_df(table_id_SYS_TPED, scenario, [year, year])
    table_id_FEC_feul = provider.get_table_id_by_name("SYS_FEC_Fuel")
    df_FEC_feul = provider.get_filtered_df(table_id_FEC_feul, scenario, [year,year])
    table_id_PWR_Gen_ELCC = provider.get_table_id_by_name('PWR_Gen-ELCC')
    df_PWR_Gen_ELCC = provider.get_filtered_df(table_id_PWR_Gen_ELCC, scenario, [year, year])

    table_id_agr = provider.get_table_id_by_name("AGR_FEC")
    df_agr = provider.get_filtered_df(table_id_agr, scenario, [year,year])
    table_id_ind = provider.get_table_id_by_name("IND_FEC")
    df_ind = provider.get_filtered_df(table_id_ind, scenario, [year,year])
    table_id_srv = provider.get_table_id_by_name("SRV_FEC")
    df_srv = provider.get_filtered_df(table_id_srv, scenario, [year,year])
    table_id_rsd = provider.get_table_id_by_name("RSD_FEC")
    df_rsd = provider.get_filtered_df(table_id_rsd, scenario, [year,year])
    table_id_tra = provider.get_table_id_by_name("TRA_FEC")
    df_tra = provider.get_filtered_df(table_id_tra, scenario, [year,year])
    list_table_ids = [table_id_SYS_TPED, table_id_FEC_feul, table_id_PWR_Gen_ELCC,
                      table_id_agr, table_id_ind, table_id_srv, table_id_rsd, table_id_tra]

    df_PWR_Gen_ELCC = prepare_elec_gen_data(df_PWR_Gen_ELCC)
    df_rsd = prepare_residential_data(df_rsd)
    df_tra = prepare_transport_data(df_tra)
    df_ind = prepare_industry_data(df_ind)
    df_agr = prepare_agriculture_data(df_agr)
    df_srv = prepare_service_data(df_srv)
   
    df_all = pd.concat([df_PWR_Gen_ELCC, df_rsd, df_tra, df_ind, df_agr, df_srv], ignore_index=True)
    df_SYS_TPED = energy_loss_calculation(df_all, df_SYS_TPED)
    df_all = pd.concat([df_all, df_SYS_TPED], ignore_index=True)
    sum_out_elec_gen = df_all[df_all['seriesTitle'] == ELECTRICITY_GENERATION]['Value'].sum()
    sum_in_elec_gen = df_all[df_all['target'] == ELECTRICITY_GENERATION]['Value'].sum()
    elec_loss = sum_in_elec_gen - sum_out_elec_gen
    
    if elec_loss >=0:
        new_row = pd.DataFrame({
        'seriesTitle': [ELECTRICITY_GENERATION],'Value': [elec_loss], 'target': [LOSS]
         })
        df_all = pd.concat([df_all, new_row], ignore_index=True)
    else:
        print("Electricity generation data inconsistency: more electricity consumed than generated. Please check the data.")
    
    sum_out_h2 = df_all[df_all['seriesTitle'] == HYDROGEN]['Value'].sum()
    sum_in_h2 = df_all[df_all['target'] == HYDROGEN]['Value'].sum()
    h2_loss = sum_in_h2 - sum_out_h2
    if h2_loss >=0:
        new_row = pd.DataFrame({
        'seriesTitle': [HYDROGEN],'Value': [h2_loss], 'target': [LOSS]
         })
        df_all = pd.concat([df_all, new_row], ignore_index=True)
    elif sum_in_h2 ==0:
        return df_all, list_table_ids
    else:
        new_row = pd.DataFrame({
        'seriesTitle': [HYDROGEN + ' source'],'Value': [-1 *h2_loss], 'target': [HYDROGEN]
         })
        df_all = pd.concat([df_all, new_row], ignore_index=True)
        print("Hydrogen generation data inconsistency: more hydrogen consumed than generated. Please check the data.")
    return df_all, list_table_ids
    
def prepare_detailed_sector_FEC(scenario, year, category, name_sub, provider = SQLDataProvider(session=session)):
    table_names = provider.check_table_include_name(scenario, category, name_sub)
    table_ids = []
    df_all = pd.DataFrame()
    for name in table_names:
        table_id = provider.get_table_id_by_name(name)
        table_ids.append(table_id)
        table_title = provider.get_table_title_by_name(name)
        df = provider.get_filtered_df(table_id, scenario, [year, year])
        text = table_title
        for word in [
            "FuelCons", "FEC", "Fuel", "consumption", "Consumption",
            "Final Energy", "final energy", " for", "_", '-','FC'
        ]:
            text = text.replace(word, " ")

        df["target"] = text.strip()
        df = df[['seriesTitle', 'Value', 'target']]
        # print(df.head(), 'df in prepare_detailed_sector_FEC')
        df_all = pd.concat([df_all, df], ignore_index=True)
    
    return df_all, table_ids


def prepare_sankey_data_energy_source_to_sector(scenario, year,provider = SQLDataProvider(session=session)):
    table_id_agr = provider.get_table_id_by_name("AGR_FEC")
    table_id_ind = provider.get_table_id_by_name("IND_FEC")
    table_id_srv = provider.get_table_id_by_name("SRV_FEC")
    table_id_rsd = provider.get_table_id_by_name("RSD_FEC")
    table_id_tra = provider.get_table_id_by_name("TRA_FEC")
    df_agr = provider.get_filtered_df(table_id_agr, scenario, [year,year])
    df_ind = provider.get_filtered_df(table_id_ind, scenario, [year,year])
    df_srv = provider.get_filtered_df(table_id_srv, scenario, [year,year])
    df_rsd = provider.get_filtered_df(table_id_rsd, scenario, [year,year])
    df_tra = provider.get_filtered_df(table_id_tra, scenario, [year,year])

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

def prepare_sankey_data_SEAI(scenario, year, provider = SQLDataProvider(session=session)):
    table_id_SYS_TPED = provider.get_table_id_by_name('SYS_TPED')
    table_id_FEC_Sector = provider.get_table_id_by_name("SYS_FEC_Sector")
    table_id_renewable = provider.get_table_id_by_name('PWR_Gen-ELCC')
    list_table_ids = [table_id_SYS_TPED, table_id_FEC_Sector, table_id_renewable]
    df_SYS_TPED = provider.get_filtered_df(table_id_SYS_TPED, scenario, [year, year])
    df_FEC_Sector = provider.get_filtered_df(table_id_FEC_Sector, scenario, [year,year])
    df_renewable = provider.get_filtered_df(table_id_renewable, scenario, [year,year])
   

    df_filtered = df_SYS_TPED[['seriesTitle','Value']].copy()
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
    return df_filtered, list_table_ids
def pastel_continuous_palette(n, s=0.35, v=0.95):
    
    colors = []
    for i in range(n):
        h = i / n                   # distribute hue 0–1
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        colors.append(f'rgb({int(r*255)}, {int(g*255)}, {int(b*255)})')
    return colors

def link_colors(df_1, df_2, series_color_map):
    level1 = df_1['seriesTitle'].unique().tolist()  
    level2 = df_1['target'].unique().tolist()       
    level3 = df_2['seriesTitle'].unique().tolist()  
    level4 = df_2['target'].unique().tolist()  
         
    nodes = list(dict.fromkeys(level1 + level2 + level3 + level4))
    node_indices = {name: i for i, name in enumerate(nodes)}

    n = len(nodes)
    fallback_colors = pastel_continuous_palette(n)
    node_colors = []
    for i, node in enumerate(nodes):
        color = normalize_series_color(series_color_map.get(node))
        node_colors.append(color if color else fallback_colors[i])
    
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


def get_sankey_title_label(title_value):
    titles = {
        0: 'Primary Energy to Demand (PJ)',
        1: 'Primary Energy to Final Energy (PJ)',
        2: 'Final Energy Consumption in Transport (PJ)',
        3: 'Final Energy Consumption in Residential (PJ)',
        4: 'Final Energy Consumption in Industry (PJ)',
    }
    return titles.get(title_value, 'Sankey Diagram')

def register_sankey_callback(app, provider = SQLDataProvider(session=session)):
    @app.callback(
        Output('scenario-sankey-dropdown', 'options'),
        Output('scenario-sankey-dropdown', 'value'),
        Input("url", "href"),
        State("scenario-sankey-dropdown", "value")
    )
    def update_sankey_scenario_options(href, current_value):
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
            # df_all = prepare_sankey_data_energy_source_to_sector(scenario, year[0], provider = provider)
            # df_all_end = prepare_sankey_data_energy_source_to_sector(scenario, year[1], provider = provider)
            df_all, list_table_ids = primary_to_final_energy_sankey(scenario, year[0], provider = provider)
            df_all_end, list_table_ids_end = primary_to_final_energy_sankey(scenario, year[1], provider = provider)

        elif title == 1:
            df_all, list_table_ids = prepare_sankey_data_SEAI(scenario, year[0], provider = provider)
            df_all_end, list_table_ids_end = prepare_sankey_data_SEAI(scenario, year[1], provider = provider)
                # Nodes
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
            draw_sankey(df_all, year[0], node, node_indices, node_colors),
            draw_sankey(df_all_end, year[1], node, node_indices, node_colors),
            start_config,
            end_config,
        )
    
