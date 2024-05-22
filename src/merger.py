import pandas as pd

all_faxes = pd.read_csv("C:/Users/Sunny/Documents/Projects/charm-fax-classifier/all_faxes.csv")
faxes_with_incomplete_names = pd.read_csv("C:/Users/Sunny/Documents/Projects/charm-fax-classifier/faxes_with_incomplete_names.csv")

column_to_match = 'File Name in Chart'
for index, row in faxes_with_incomplete_names.iterrows():
    relevant_rows = all_faxes[all_faxes[column_to_match] == str(row[column_to_match])]
    print(row[column_to_match], relevant_rows)