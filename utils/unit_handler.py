
dict_unit = {
    "PJ": 1,
    "TWh": 0.28,
    "ktoe": 23.9,
    "kt": 1,
    "Mt": 0.001
}
def unit_detect(selected_label,df):
   

    if selected_label in dict_unit.keys():
        df["Value"] *= dict_unit[selected_label]
        df["label"] = selected_label
    
    return df
    