
def filter_df_by_category(df, existing_words=[], non_existing_words=[]):
    filtered_df = df
    
    existing_words = [word.lower() for word in existing_words]
    non_existing_words = [word.lower() for word in non_existing_words]
    if existing_words:
        for word in existing_words:
            filtered_df = filtered_df[filtered_df['category'].apply(lambda x: any(word in item for item in x))]

    if non_existing_words:
        for word in non_existing_words:
            filtered_df = filtered_df[filtered_df['category'].apply(lambda x: not any(word in item for item in x))]
    return filtered_df

import pandas as pd

def filter_df_for_search(df, existing_words=None, non_existing_words=None, 
                          search_columns=["category", "tableTitle"]):
    
    if existing_words is None:
        existing_words = []
    if non_existing_words is None:
        non_existing_words = []

    # Convert all to lowercase for case-insensitive matching
    existing_words = [w.lower() for w in existing_words]
    non_existing_words = [w.lower() for w in non_existing_words]

    filtered_df = df.copy()

    # Include filter — at least one of the include words should appear
    if existing_words:
        include_pattern = "|".join(existing_words)
        include_mask = filtered_df[search_columns].apply(
            lambda col: col.astype(str).str.lower().str.contains(include_pattern, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[include_mask]

    # Exclude filter — none of the exclude words should appear
    if non_existing_words:
        exclude_pattern = "|".join(non_existing_words)
        exclude_mask = filtered_df[search_columns].apply(
            lambda col: col.astype(str).str.lower().str.contains(exclude_pattern, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[~exclude_mask]

    return filtered_df
