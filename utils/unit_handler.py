
def unit_detect(label, selected_label,df):
    value = 0
    unit = ""
    dict_unit = {
        "K": 1,
        "M": 10**3,
        "G": 10**6,
        "T": 10**9,
        "P": 10**12
    }
    
    if label == "kt":
        value = 1
        unit += "t"
    elif label =="PJ":
        value = 10**12
        unit += "J"
    elif label == "GW":
        value = 10**6
        unit += "W"
    s_label = selected_label[0]
    print(df["Value"].iloc[0], "before")
    
    df["Value"] = df["Value"]*value
    print(df["Value"].iloc[0], "middle")
    print(selected_label)
    print(dict_unit[selected_label])
    df["Value"] = df["Value"]/dict_unit[selected_label]
    print(df["Value"].iloc[0], "after")

    df['label'] = s_label + unit
    return df
    