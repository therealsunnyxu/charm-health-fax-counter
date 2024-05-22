import pandas as pd
from rapidfuzz import fuzz, process
import string
from collections import Counter

faxes = pd.read_csv("C:/Users/Sunny/Documents/Projects/charm-fax-classifier/faxes.csv")
names = pd.read_csv("C:/Users/Sunny/Documents/Projects/charm-fax-classifier/PatientsDetails_21May2024.csv")
faxes = faxes.drop('Index',axis=1)
faxes['Date'] = faxes['Date'].str.split().str[:3].str.join(sep=' ')
faxes_with_names = faxes[faxes['File Name in Chart'].notna() & faxes['Patient Name'].isna()]
faxes_with_names['File Name in Chart'] = faxes_with_names['File Name in Chart'].str.translate(str.maketrans('', '', string.punctuation)).str.replace('\s+', ' ',regex=True).str.replace('[0-9]', '', regex=True)

word_counter = Counter()

threshold = 80

last_names = names['LastName'].unique().tolist()
for index, row in faxes_with_names.iterrows():
    file_name = row['File Name in Chart']
    words = [x for x in file_name.split()]
    last_name_matches = [x for x in words if x in last_names]
    if len(last_name_matches) > 0:
        faxes_with_names.at[index, 'Patient Name'] = last_name_matches[0]
    else:
        # no last name matches, go to next file name
        continue

    first_name_initials = [x for x in words if len(x) == 1]

    first_names = names[names['LastName'] == last_name_matches[0]]['FirstName'].tolist()
    first_name_matches = [x for x in words if x in first_names]
    if len(first_name_matches) > 0:
        faxes_with_names.at[index, 'Patient Name'] = first_name_matches[0] + " " + faxes_with_names.at[index, 'Patient Name']
        # first name gotten, continue to next file name
        continue

    # continue to matching single letters as initials
    #print(first_name_initials, first_names)
    first_name_initial_match = [x for x in first_names if x[0] in first_name_initials]
    if len(first_name_initial_match) > 0:
        #print(first_name_initial_match[0] + " " + faxes_with_names.at[index, 'Patient Name'], faxes_with_names.at[index, 'Patient Name'])
        faxes_with_names.at[index, 'Patient Name'] = first_name_initial_match[0] + " " + faxes_with_names.at[index, 'Patient Name']
        continue
        
    """
    #print(last_name_matches[0], file_name)
    # now do fuzzy matching for words before and after the last names
    last_name_index = words.index(last_name_matches[0])
    first_word, last_word = "", ""
    if len(words) <= 1:
        continue
        
    if last_name_index < len(words) - 1:
        last_word = words[last_name_index+1]
    if last_name_index > 0:
        first_word = words[last_name_index-1]
    matches = process.extract(first_word + " " + last_word, first_names)
    #print(matches, file_name)
    """


faxes.update(faxes_with_names)
faxes.to_csv('test.csv', index=False)
faxes_without_names = faxes[faxes['Patient Name'].isna()]
faxes_with_incomplete_names = faxes[faxes['Patient Name'].str.split().str.len() == 1]
faxes_with_incomplete_names.to_csv('faxes_with_incomplete_names.csv', index=False)
