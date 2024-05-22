import pandas as pd

all_faxes = pd.read_csv("C:/Users/Sunny/Documents/Projects/charm-fax-classifier/all_faxes.csv")

no_dups = all_faxes.drop_duplicates('File Name in Internal System')
no_dups.to_csv('no_dups.csv', index=False)