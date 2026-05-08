
import plotly.graph_objects as go
import pandas as pd
import colorsys
from data_provider.sql_data import SQLDataProvider
from auth.models import db, normalize_series_color


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
    """Convert electricity generation rows into Sankey flows toward electricity and hydrogen."""
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
    """Map residential fuel-consumption rows into Sankey source-to-sector flows."""
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
    """Map transport fuel-consumption rows into Sankey source-to-sector flows."""
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
    """Map industry fuel-consumption rows into Sankey source-to-sector flows."""
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
    """Map agriculture fuel-consumption rows into Sankey source-to-sector flows."""
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
    """Map services fuel-consumption rows into Sankey source-to-sector flows."""
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
    """Calculate remaining primary energy flows after final demand is subtracted."""
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
   
    return df_SYS_TPED[['seriesTitle', 'Value', 'target']]

def primary_to_final_energy_sankey(scenario, year, provider = SQLDataProvider(session=session)):
    """Build primary-energy-to-demand Sankey flow data and source table IDs.
    This function prepares the data for the Sankey diagram by fetching and processing the relevant tables 
    for the given scenario and year.
    It also includes electricity losses and hydrogen losses.
    It returns a DataFrame with the flow data and a list of table IDs that were used in the preparation.
    """
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

    # Calculate electricity losses and add as a separate flow if needed
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
    
    # Calculate hydrogen losses and add as a separate flow if needed
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
    """Build detailed final-energy-consumption flows for matching sector tables."""
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
        df_all = pd.concat([df_all, df], ignore_index=True)
    
    return df_all, table_ids


def prepare_sankey_data_energy_source_to_sector(scenario, year,provider = SQLDataProvider(session=session)):
    """Build source-to-sector final energy flows across main demand sectors.
    This function was not called and only kept for possible future use if we want to have a sankey with only energy sources and demand sectors without detailed breakdown.
    """
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
    """Convert negative electricity rows into positive export flows."""
    if not df_filtered[df_filtered['Value'] < 0].empty:
        neg_row = df_filtered[df_filtered['Value'] < 0].iloc[0]
        
        seriesTitle = neg_row['seriesTitle' ]+ ' Export'
        target = neg_row['target']
        value = -neg_row['Value']  
        df_filtered.loc[len(df_filtered)] = [target, value, seriesTitle]
        df_filtered = df_filtered.drop(neg_row.name)
    
    return df_filtered

def prepare_sankey_data_SEAI(scenario, year, provider = SQLDataProvider(session=session)):
    """Build SEAI-style primary-energy-to-final-energy Sankey flow data."""
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

    # If "Other renewables" is present, we need to break it down into its main components and adjust the value accordingly for wind and solar.
    # This is because in the data, "Other renewables" includes wind and solar, but we want to show them separately in the Sankey diagram.
    # We will subtract the wind and solar values from "Other renewables" to avoid double counting.
    if "Other renewables" in df_filtered['seriesTitle'].unique():       
        df_filtered.loc[df_filtered['seriesTitle']== "Wind offshore", 'Value'] = df_renewable[df_renewable['seriesTitle']== "Wind offshore"]['Value'].iloc[0]
       
        df_filtered.loc[df_filtered['seriesTitle']== "Wind onshore", 'Value'] = df_renewable[df_renewable['seriesTitle']== "Wind onshore"]['Value'].iloc[0]
        df_filtered.loc[df_filtered['seriesTitle']== "Solar", 'Value']= df_renewable[df_renewable['seriesTitle']== "Solar"]['Value'].iloc[0]
        sum_renewable = (df_renewable[df_renewable['seriesTitle']== "Wind offshore"]['Value'].iloc[0] + df_renewable[df_renewable['seriesTitle']== "Wind onshore"]['Value'].iloc[0] + 
                        df_renewable[df_renewable['seriesTitle']== "Solar"]['Value'].iloc[0])
        df_filtered.loc[df_filtered['seriesTitle']== "Other renewables", 'Value'] = df_filtered[df_filtered['seriesTitle']== "Other renewables"]['Value'].iloc[0] - sum_renewable
    
    # Now we will add the flows from primary energy to final energy for each sector based on the values in df_FEC_Sector.
    # The "Value" column in df_FEC_Sector represents the final energy consumption for each sector.
    # We will use that as the flow value from primary energy to final energy for each sector.
    new_rows = pd.DataFrame({
        'Value': df_FEC_Sector['Value'],             # Value from df_FEC_Sector
        'seriesTitle': 'Final Energy',                # new column with constant value
        'target': df_FEC_Sector['seriesTitle']        # target column
    })

    df_filtered = pd.concat([df_filtered, new_rows], ignore_index=True)
    
    # Finally, we will calculate the loss as the difference between primary energy and final energy (including electricity export if present) and add it as a separate flow from primary energy to loss.
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


def pastel_continuous_palette_rgb(n, s=0.35, v=0.95):
    """Generate n evenly spaced pastel colors as Plotly-compatible RGB strings."""
    
    colors = []
    for i in range(n):
        h = i / n                   # distribute hue 0–1
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        colors.append(f'rgb({int(r*255)}, {int(g*255)}, {int(b*255)})')
    return colors

def link_colors(df_1, df_2, series_color_map):
    """Create shared Sankey nodes, node indexes, and node colors for two diagrams."""
    level1 = df_1['seriesTitle'].unique().tolist()  
    level2 = df_1['target'].unique().tolist()       
    level3 = df_2['seriesTitle'].unique().tolist()  
    level4 = df_2['target'].unique().tolist()  
         
    nodes = list(dict.fromkeys(level1 + level2 + level3 + level4))
    node_indices = {name: i for i, name in enumerate(nodes)}

    n = len(nodes)
    fallback_colors = pastel_continuous_palette_rgb(n)
    node_colors = []
    for i, node in enumerate(nodes):
        color = normalize_series_color(series_color_map.get(node))
        node_colors.append(color if color else fallback_colors[i])
    
    return nodes, node_indices, node_colors
def compute_node_totals(df, nodes):
    """Calculate display totals for Sankey nodes from incoming and outgoing flows."""
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
def draw_sankey(df_all, year, nodes, node_indices, node_colors, scenario=None, title_label=None):
    """Render a Plotly Sankey figure for one year of prepared flow data."""
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
    title_parts = [part for part in [scenario, title_label, str(year) if year is not None else None] if part]
    fig.update_layout(
        title=" | ".join(title_parts) if title_parts else str(year)
    )
    return fig


def get_sankey_title_label(title_value):
    """Return the human-readable label for a Sankey view selector value."""
    titles = {
        0: 'Primary Energy to Demand (PJ)',
        1: 'Primary Energy to Final Energy (PJ)',
        2: 'Final Energy Consumption in Transport (PJ)',
        3: 'Final Energy Consumption in Residential (PJ)',
        4: 'Final Energy Consumption in Industry (PJ)',
    }
    return titles.get(title_value, 'Sankey Diagram')
