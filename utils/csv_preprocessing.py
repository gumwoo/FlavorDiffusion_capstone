import pandas as pd
import re

def readingCSV(file_path):
    df = pd.read_csv(file_path, encoding="utf-8", skiprows=2)

    start_index = df.columns.get_loc("Concentration2)")

    row_index = 0
    non_null_col_count = df.iloc[row_index].count()

    liquors = df.iloc[row_index, start_index:start_index + non_null_col_count].tolist()
    liquors = [liquor.strip() for liquor in liquors]

    for i, new_col in enumerate(liquors):
        df.columns.values[start_index + i] = new_col

    df.columns = df.columns.str.strip()
    df = df.drop(0)
    
    compound_col = "Compound name"

    pairings = []

    for _, row in df.iterrows():
        compound_name = row[compound_col]

        for liquor in liquors:
            if pd.notna(row[liquor]):
                pairings.append({"Compound": compound_name.strip().replace(' ', '_').lower(), "Liquor": re.sub(r'\s?\(.*?\)', '', liquor)})

    pairings_df = pd.DataFrame(pairings)

    pairings_df.to_csv("c:/Users/user/Desktop/FlavorDiffusion/FlavorDiffusion/dataset/compound_liquor_pairing.csv", index=False, encoding="utf-8")

if __name__ == "__main__":
    readingCSV("c:/Users/user/Desktop/FlavorDiffusion/FlavorDiffusion/dataset/향기성분 프로파일_v250319.csv")