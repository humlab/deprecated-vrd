# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
from ipywidgets import FileUpload
from IPython.display import display

file_upload = FileUpload(
    accept='.csv',  # Accepted file extension e.g. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
    multiple=False  # True to accept multiple files upload else False
)

display(file_upload)

# %%
filename = next(iter(file_upload.value))
print(f'"{filename}" uploaded!')

from pathlib import Path

CSV_DIRECTORY = Path('csv')
CSV_DIRECTORY.mkdir(exist_ok=True)

content = file_upload.value[filename]['content']
with open(f'csv/{filename}', 'wb') as f: f.write(content)

# %%
import pandas as pd

df = pd.read_csv(f'csv/{filename}')
df.head()  # Feel free to comment this out by prefixing the row with a '#' character


# %% [markdown]
# Remove all lines where similarity score is zero,

# %%
def number_of_rows(dataframe):
    return len(dataframe.index)

# Here we remove all rows with a similarity score of zero (0) as they
# are not considered pertinent to our efforts
no_of_lines_before_drop = number_of_rows(df)
df.drop(df[df['Similarity Score'] == 0].index, inplace=True)
print(f'Removed {no_of_lines_before_drop - number_of_rows(df)} lines')
display(df.info())
df.head()

# %%
from video_reuse_detector.fingerprint import MatchLevel

def sort_by_similarity_score(df):
    # Make the best similarity score appear first
    return df.sort_values(by=['Similarity Score', 'Query Segment Id', 'Reference Segment Id'], ascending=False)

def groupby_matchlevel(df):
    return df.groupby(df['Match Level'])

def split_by_matchlevel(df):
    grouped = groupby_matchlevel(df)
    matchlevel_to_df = {}
    
    # All match levels may not be present,
    for match_level in MatchLevel:
        try:
            matchlevel_to_df[match_level] = sort_by_similarity_score(grouped.get_group(str(match_level)))
        except KeyError as e:
            # No matches for the given level
            matchlevel_to_df[match_level] = pd.DataFrame([])
            
    return matchlevel_to_df

# This will contain all the dataframes,
dfs = {}

query_video_names = list(df['Query Video Name'].unique())
reference_video_names = list(df['Reference Video Name'].unique()) 
all_video_names = set(query_video_names + reference_video_names)
print(all_video_names)

# We group by all the video pair-wise comparisons
grouped_by_name_pairs = df.groupby(['Query Video Name', 'Reference Video Name'])

# Example:
display(grouped_by_name_pairs.get_group(('ATW-644.mp4', 'ATW-644_hflip.mp4')))

# %%
# This code will help us identify continous sequences of
# video that are matching

QUERY_SEGMENT_ID_COLUMN = 'Query Segment Id'
REFERENCE_SEGMENT_ID_COLUMN = 'Reference Segment Id'

def find_islands(df): # yields a dataframe
    import numpy as np # for np.nan

    def get_island(col):
        return (~col.diff().between(-1,1)).cumsum()

    df[['Q Island', 'R Island']] = df[[QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN]].apply(get_island)

    result = df.groupby(['Q Island', 'R Island']) \
                .agg(**{
                    'Q Start': (QUERY_SEGMENT_ID_COLUMN, 'first'),
                    'Q End': (QUERY_SEGMENT_ID_COLUMN, 'last'),
                    'R Start': (REFERENCE_SEGMENT_ID_COLUMN, 'first'),
                    'R End': (REFERENCE_SEGMENT_ID_COLUMN, 'last'),
                    'Count': (QUERY_SEGMENT_ID_COLUMN, 'count')
                }) \
                .replace({'Count': 1}, {'Count': np.nan}) \
                .dropna()

    result['Q'] = result[['Q Start', 'Q End']].apply(tuple, axis=1)
    result['R'] = result[['R Start', 'R End']].apply(tuple, axis=1)

    return result

# isolate the boundaries of the islands
def island_boundaries(islands): # Ingest the result from find_islands 
    df = islands.reset_index()
    return df[['Q', 'R']]


# %%
import pandas as pd 
from collections import namedtuple

QUERY_SEGMENT_ID_COLUMN = 'Query Segment Id'
REFERENCE_SEGMENT_ID_COLUMN = 'Reference Segment Id'
columns = [QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN]

def test(test_data_provider):
    data, expected_islands = test_data_provider()
    df = pd.DataFrame(data, columns=columns)
    display(df)
    islands = find_islands(df)
    display(islands)
    display(island_boundaries(islands))
        
def without_pattern():
    # No sequence in either column. No results
    return ([[1, 2], [7, 0], [3, 6]], [])

def pseudo_pattern_query():
    # Sequence in first column, but no sequence in second column. No results
    return ([[1, 2], [2, 0], [3, 6]], [])

def pseudo_pattern_reference():
    # Sequence in second column, but no sequence in first column. No results
    return ([[1, 2], [7, 3], [3, 4]], [])

def pseudo_pattern_query_broken():
    # Broken sequence in first column, sequence in second column. No results
    return ([[1, 2], [3, 3], [7, 4]], [])

def pattern_asc():
    # Sequence occurs in both columns, asc. Expect results
    return ([[1, 2], [2, 3], [3, 4]], [((1, 3), (2, 4))])


def pattern_desc():
    # Sequence occurs in both columns, desc. Expect results
    return ([[1, 4], [2, 3], [3, 2]], [((1, 3), (4, 2))])

def pattern_and_noise():
    # There is a sequence, andreturnnoise. Expect results
    return ([[1, 0], [1, 4], [1, 2], [1, 3], [2, 3], [3, 4]], [((1, 3), (2, 4))])

def multiple_contiguous_sequences():
    return [[1, 1], [2, 2], [3, 3], [0, 4], [1, 5], [2, 6], [3, 7], [4, 8]]

#test(without_pattern)
#test(pseudo_pattern_query)
#test(pseudo_pattern_reference)
#test(pseudo_pattern_query_broken)
#test(pattern_asc)
#test(pattern_desc)
#test(pattern_and_noise)
#test(multiple_contiguous_sequences)
awesome_matches = split_by_matchlevel(grouped_by_name_pairs.get_group(('ATW-644.mp4', 'ATW-644_hflip.mp4')))[MatchLevel.LEVEL_A].sort_values(by=['Query Segment Id', 'Reference Segment Id'])
display(find_islands(awesome_matches[awesome_matches['Similarity Score'] > 0.95]))
#display(find_islands(split_by_matchlevel(grouped_by_name_pairs.get_group(('ATW-644.mp4', 'ATW-644_hflip.mp4')))[MatchLevel.LEVEL_A]))
#display(find_islands(grouped_by_name_pairs.get_group(('ATW-650.mp4', 'ATW-550_cartoon.mp4'))))


# %%
import qgrid

#qgrid.show_grid(dfs['ATW-hflip.mp4'][MatchLevel.LEVEL_A])
qgrid.show_grid(grouped_by_name_pairs.get_group(('ATW-644.mp4', 'ATW-644_hflip.mp4')))

# %%
