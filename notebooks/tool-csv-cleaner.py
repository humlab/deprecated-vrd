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

SIMILARITY_SCORE_COLUMN = 'Similarity Score'
QUERY_SEGMENT_ID_COLUMN = 'Query Segment Id'
REFERENCE_SEGMENT_ID_COLUMN = 'Reference Segment Id'
query_video_duration = df[QUERY_SEGMENT_ID_COLUMN].max()
reference_video_duration = df[REFERENCE_SEGMENT_ID_COLUMN].max()

# Here we remove all rows with a similarity score of zero (0) as they
# are not considered pertinent to our efforts
no_of_lines_before_drop = number_of_rows(df)
df.drop(df[df[SIMILARITY_SCORE_COLUMN] == 0].index, inplace=True)
print(f'Removed {no_of_lines_before_drop - number_of_rows(df)} lines')
display(df.info())
df.head()

# %%
from video_reuse_detector.fingerprint import MatchLevel

QUERY_VIDEO_NAME_COLUMN = 'Query Video Name'
REFERENCE_VIDEO_NAME_COLUMN = 'Reference Video Name'

def sort_by_similarity_score(df):
    # Make the best similarity score appear first
    return df.sort_values(by=[SIMILARITY_SCORE_COLUMN, 
                              QUERY_SEGMENT_ID_COLUMN,
                              REFERENCE_SEGMENT_ID_COLUMN],
                          ascending=False)

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

def get_best_matches(df):
    return sort_by_similarity_score(split_by_matchlevel(df)[MatchLevel.LEVEL_A])

def get_best_matches_for_pair(name_pair, grouped_by_name_pairs):
    return get_best_matches(grouped_by_name_pairs.get_group((name_pair)))

def get_all_names(df):
    query_video_names = list(df[QUERY_VIDEO_NAME_COLUMN].unique())
    reference_video_names = list(df[REFERENCE_VIDEO_NAME_COLUMN].unique()) 
    return set(query_video_names + reference_video_names)

# We group by all the video pair-wise comparisons
grouped_by_name_pairs = df.groupby([QUERY_VIDEO_NAME_COLUMN, REFERENCE_VIDEO_NAME_COLUMN])

all_groups = grouped_by_name_pairs.groups.keys()
first_pair = next(iter(all_groups))

# Example:
display(get_best_matches_for_pair(first_pair, grouped_by_name_pairs))


# %%
def group_into_sequences(seq):
    """
    Takes a sequence seq and groups it into unbroken subsequences
    
    >>> group_into_sequences([2, 8, 9, 10, 11, 12]))
    [[2], [8, 9, 10, 11, 12]]
    """
    # https://stackoverflow.com/a/3149493/5045375
    from operator import itemgetter
    from itertools import groupby
    
    lst = []
    
    for k, g in groupby(enumerate(seq), lambda x: x[0]-x[1]):
        lst.append(list(map(itemgetter(1), g)))
    
    return list(lst)
    
def find_islands(pair_matches_df):
    from collections import defaultdict
    #query_segment_id_boundaries = (0, pair_matches_df[QUERY_SEGMENT_ID_COLUMN].max())
    #reference_segment_id_boundaries = (0, pair_matches_df[REFERENCE_SEGMENT_ID_COLUMN].max())
    
    # Ensure sorted
    df = sort_by_similarity_score(pair_matches_df)
    
    #observed_query_segment_ids = [None] * (query_segment_id_boundaries[1] + 1)
    #observed_reference_segment_ids = [None] * (reference_segment_id_boundaries[1] + 1)
    
    # Start with the best conceivably match and try to find islands
    query_segment_id_to_reference_segment_ids_map = defaultdict(list)
    
    for _, row in df.iterrows():
        query_segment_id = row[QUERY_SEGMENT_ID_COLUMN]
        reference_segment_id = row[REFERENCE_SEGMENT_ID_COLUMN]
        query_segment_id_to_reference_segment_ids_map[query_segment_id].append(reference_segment_id)
    
    query_segment_id_to_reference_segment_ids_map = {k: sorted(v) for k, v in query_segment_id_to_reference_segment_ids_map.items()}
    
    # These can be discontinuous, for instance
        #
        # query_segment_id_to_reference_segment_ids_map[3] could map to
        # [2, 3, 7, 8, 9]
        #       ^
        #      hole
        #
        # so we first isolate the islands in each respective list, i.e. so we get
        #
        # [[2, 3], [7, 8, 9]]
    query_segment_id_to_reference_segment_ids_map = {k: group_into_sequences(v) for k, v in query_segment_id_to_reference_segment_ids_map.items()}
    
    # Recreate the default dict
    query_segment_id_to_reference_segment_ids_map = defaultdict(list, query_segment_id_to_reference_segment_ids_map)
    print(query_segment_id_to_reference_segment_ids_map)
    # Iterate through the keys, and see if it can be merged together with its neighbours to create
    # overlap/continuation of sequence
    for idx in range(1, len(query_segment_id_to_reference_segment_ids_map.keys())):
        # We now have sublists, see above comment, and should be able to check for
        # overlap
        previous_ref_ids = query_segment_id_to_reference_segment_ids_map[idx - 1]
        these_ref_ids = query_segment_id_to_reference_segment_ids_map[idx]
        
        if len(previous_ref_ids) == 0 or len(these_ref_ids) == 0:
            continue
            
        for asc_seq_prev in previous_ref_ids:
            for asc_seq_curr in these_ref_ids:
                if set(asc_seq_prev).isdisjoint(asc_seq_curr):
                    # No overlap between sequences, end sequence boundary
                    continue
                else:
                    # Complete or partial overlap, continue sequence boundary
                    end = idx
                    

    # Continue with the next best match, see if that has already been included
    # in a previous island, and if not, create a new one.
    return 1, 1

def are_overlapping_sequences(seq1, seq2):
    return not set(seq1).isdisjoint(seq2)

def are_adjacent_sequences(seq1, seq2):
    return abs(seq1[-1] - seq2[0]) == 1

def is_continuation_of_sequence(this, that):
    return are_overlapping_sequences(this, that) or are_adjacent_sequences(this, that)

def find_sequenced_matches(pair_matches_df):
    from collections import defaultdict

    # Ensure sorted
    df = sort_by_similarity_score(pair_matches_df)
    
    raw_matches = defaultdict(list)
    
    # First, we gather up a dictionary, such that
    #
    # raw_matches[query_segment_id] = [reference_ids]
    #
    # for all the ids that it matches
    for _, row in df.iterrows():
        query_segment_id = row[QUERY_SEGMENT_ID_COLUMN]
        reference_segment_id = row[REFERENCE_SEGMENT_ID_COLUMN]
        similarity_score = row[SIMILARITY_SCORE_COLUMN]
        
        #raw_matches[query_segment_id].append((similarity_score, reference_segment_id))
        raw_matches[query_segment_id].append(reference_segment_id)
        
    # We now have a dictionary where it's difficult to study if there are
    # sequences between adjacent pairs of segment ids, because in [reference_ids]
    # in the below line there is no structure
    #
    # raw_matches[query_segment_id] = [reference_ids]
    #
    # we instead want
    #
    # matches[query_segment_id] = [[ref_ids], [other_ref_ids], ...]
    #
    # where each sublist is a sequence of incrementing ids
    #
    # This will make it easier to detect overlap between matches[x] and matches[x+1]
    matches = {k: sorted(v) for k, v in raw_matches.items()}
    matches = {k: group_into_sequences(v) for k, v in matches.items()}
    matches = defaultdict(list, matches)
    
    # Then, we iterate over matches[x] for all x and compare against
    # the previously observed reference ids. If possible, we want to see
    # if we can build a continued sequence of matches.
    found_sequences = []
    q_start = None
    q_stop = None
    r_start = None
    r_stop = None
    
    sequences_found = []
    
    # Keep a running tally of the sequences we are currently "building"
    sequences_being_observed = {}
    
    for i in range(1, len(matches.keys())):
        previous_reference_ids = matches[i - 1]
        these_reference_ids = matches[i]
        
        found_continuation_between_ids = False
        
        for asc_seq_prev in previous_reference_ids:
            for asc_seq_curr in these_reference_ids:
                if is_continuation_of_sequence(asc_seq_prev, asc_seq_curr):
                    for seq in sequences_being_observed[i][0]:
                        # This will be true for at least one element
                        if is_continuation_of_sequence(asc_seq_curr, seq):
                            
                    
                    if q_start is None:
                        q_start = i
                    if r_start is None:
                        r_start = asc_seq_prev[0]
                    
                    r_stop = asc_seq_curr[-1]
                    found_continuation_between_ids = True
        
        if found_continuation_between_ids:
            q_stop = i - 1
                    
            if q_start is None: # Also true, r_start and r_stop == None
                # We haven't observed a sequence yet but haven't found
                # any overlaps either
                continue
                        
            sequences_found.append((q_start, q_stop, r_start, r_stop))
                    
            q_start = None
            r_start = None
            r_stop = None
    
    return sequences_found
                    
        
"""    
def cull_non_sequenced_matches(pair_matches_df):
    df = sort_by_similarity_score(pair_matches_df)
    
    for _, row in df.iterrows():
        query_segment_id = row[QUERY_SEGMENT_ID_COLUMN]
        reference_segment_id = row[REFERENCE_SEGMENT_ID_COLUMN]
        similarity_score = row[SIMILARITY_SCORE_COLUMN]
        
        if query_segment_id + 1 in df[QUERY_SEGMENT_ID_COLUMN].values or query_segment_id - 1 in df[QUERY_SEGMENT_ID_COLUMN].values:
"""
    

def create_heatmap(pair_matches_df):
    # Ensure sorted
    df = sort_by_similarity_score(pair_matches_df)
    
    max_query_segment_id = df[QUERY_SEGMENT_ID_COLUMN].max()
    max_reference_segment_id = df[REFERENCE_SEGMENT_ID_COLUMN].max()

    query_heatmap = [0] * (max_query_segment_id + 1)
    reference_heatmap = [0] * (max_reference_segment_id + 1)
    
    row_count = len(df.index)
    
    row_idx_iteration_order = row_count
    for _, row in df.iterrows():
        query_segment_id = row[QUERY_SEGMENT_ID_COLUMN]
        reference_segment_id = row[REFERENCE_SEGMENT_ID_COLUMN]
        similarity_score = row[SIMILARITY_SCORE_COLUMN]
        
        weighted_score = similarity_score * row_idx_iteration_order / row_count
        row_idx_iteration_order -= 1
        query_heatmap[query_segment_id] += weighted_score
        reference_heatmap[reference_segment_id] += weighted_score
        
    return query_heatmap, reference_heatmap
    
print(find_sequenced_matches(get_best_matches_for_pair(first_pair, grouped_by_name_pairs)))
#print(group_into_sequences([2, 8, 9, 10, 11, 12]))
"""q_h, r_h = create_heatmap(get_best_matches_for_pair(first_pair, grouped_by_name_pairs))
import numpy as np
from matplotlib import pyplot as plt

indices = np.arange(max(query_video_duration, reference_video_duration) + 1)
print(query_video_duration)
print(reference_video_duration)
r_h += [0] * (len(q_h) - len(r_h))

fig, axs = plt.subplots(1, 1)

plt.bar(indices, list(q_h), color="orangered", alpha=0.5)
plt.bar(indices, list(r_h), color='mediumslateblue', alpha=0.5)
        
plt.sca(axs)
plt.tick_params(
        axis='y',          # changes apply to the y-axis
        which='both',      # both major and minor ticks are affected
        left=False,        # ticks along the left edge are off
        right=False,       # ticks along the right edge are off
        labelleft=False)   # labels along the left edge are off        
#plt.xticks(indices, CORRELATION_CASES, rotation='vertical')"""

# %%
# This code will help us identify continous sequences of
# video that are matching

def find_islands(df): # yields a dataframe
    import numpy as np # for np.nan

    def get_island(col):
        return (~col.diff().between(-1,1)).cumsum()

    df = df.sort_values(by=[QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN])
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
#name_pair = ('5c5714c0a56fd2a96f99db2f59b0d03659d77cdf.flv', '6d1a89c83d554fc6a5e39fcadb172a79baf140fd.mp4')


"""
def find_consecutive_matches(df):
    QUERY_SEGMENT_ID_COLUMN = 'Query Segment Id'
    REFERENCE_SEGMENT_ID_COLUMN = 'Reference Segment Id'
    
    sorted_by_ids = df.sort_values(by=[QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN])
    sequences = []
    
    def parse_row(previous_query_segment_id, 
                  previous_reference_ids, 
                  rows):
        head, *tail = rows
        _, row = head
    
        #print(f'Processing {row}')
        current_query_segment_id = row[QUERY_SEGMENT_ID_COLUMN]
        
        if previous_query_segment_id is not None:
            # Special: first invocation of function
            previous_query_segment_id = current_query_segment_id
            previous_reference_ids.append([row[REFERENCE_SEGMENT_ID]])
        
            # Continue parsing next row
            return lambda: parse_row(previous_query_segment_id, 
                  previous_reference_ids,
                  tail)

        if previous_query_segment_id == current_query_segment_id:
            # Continue adding upp reference ids
            previous_reference_ids.append([row[REFERENCE_SEGMENT_ID]])
        
            # Continue parsing next row
            return lambda: parse_row(previous_query_segment_id, 
                  previous_reference_ids,
                  tail)
        
        if previous_query_segment_id + 1 == current_query_segment_id:
            # See if the currently observed reference segment id forms a continuation
            # of one of the sequences gathered earlier
            for seq in previous_reference_ids:
                
        else:
            # End of "island"
        
        return lambda: parse_row(previous_query_segment_id, 
                  previous_reference_ids,
                  tail)
    
    next_call = parse_row(None, None, [], [], None, sorted_by_ids.iterrows())
    next_call()"""
    
# 1. You read the first line, for a certain query_segment_id
# 2. You take _all_ reference segment ids that query_segment_id "points" to. Create one list
#    for each reference segment id, and, add the reference segment id to the start of the list
# 3a. You either read a segment id that is _next_ (i.e., one larger than your previous one)
# 3b. You read a segment id that is at least one removed from your previous one
#
# If, 3a.
#
# 3a1. you read all the reference segment ids that one relates to **and**, to your previous
#      batch of reference ids, you append any numbers that would create an unbroken sequence

#sorted_by_ids = df.sort_values(by=[QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN])

awesome_matches = sort_by_similarity_score(get_best_matches_for_pair(first_pair, grouped_by_name_pairs))

#awesome_matches = awesome_matches[awesome_matches[SIMILARITY_SCORE_COLUMN] > 0.8]
#find_consecutive_matches(awesome_matches)
#qgrid.show_grid(awesome_matches.sort_values(by=[QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN]))
import qgrid
qgrid.show_grid(find_islands(awesome_matches))

#qgrid.show_grid(awesome_matches)
#display(find_islands(split_by_matchlevel(grouped_by_name_pairs.get_group(('ATW-644.mp4', 'ATW-644_hflip.mp4')))[MatchLevel.LEVEL_A]))
#display(find_islands(grouped_by_name_pairs.get_group(('5c5714c0a56fd2a96f99db2f59b0d03659d77cdf.flv', '6d1a89c83d554fc6a5e39fcadb172a79baf140fd.mp4'))))


# %%
awesome_matches = get_best_matches_for_pair(name_pair, grouped_by_name_pairs)

"""
def groupby_query_segment_id(df):
    return df.groupby(df[QUERY_SEGMENT_ID_COLUMN])

grouped_by_query_segment_id = groupby_query_segment_id(awesome_matches)

reference_ids_for_group = list(grouped_by_query_segment_id.get_group(2)[REFERENCE_SEGMENT_ID_COLUMN])
sequences = [[x] for x in reference_ids_for_group]
display(sequences)

reference_ids_for_group = list(grouped_by_query_segment_id.get_group(3)[REFERENCE_SEGMENT_ID_COLUMN])

for seq in sequences:
    for ref_id in reference_ids_for_group:
        if seq[-1] + 1 == ref_id:
            seq.append(ref_id)

display(sequences)

reference_ids_for_group = list(grouped_by_query_segment_id.get_group(4)[REFERENCE_SEGMENT_ID_COLUMN])

for seq in sequences:
    for ref_id in reference_ids_for_group:
        if seq[-1] + 1 == ref_id:
            seq.append(ref_id)

display(sequences)
            
reference_ids_for_group = list(grouped_by_query_segment_id.get_group(5)[REFERENCE_SEGMENT_ID_COLUMN])

for seq in sequences:
    for ref_id in reference_ids_for_group:
        if seq[-1] + 1 == ref_id:
            seq.append(ref_id)

display(sequences)

reference_ids_for_group = list(grouped_by_query_segment_id.get_group(6)[REFERENCE_SEGMENT_ID_COLUMN])

for seq in sequences:
    for ref_id in reference_ids_for_group:
        if seq[-1] + 1 == ref_id:
            seq.append(ref_id)

display(sequences)
""""""
for _, row in awesome_matches.sort_values(by=['Similarity Score']).iter:
    query_segment_id = row[QUERY_SEGMENT_ID_COLUMN]
    if query_segment_id in islands:
        continue
    else:
        observed_query_ids[query_segment_ids] = row[REFERENCE_SEGMENT_ID_COLUMN]"""
    

qgrid.show_grid(awesome_matches.sort_values(by=[QUERY_SEGMENT_ID_COLUMN, REFERENCE_SEGMENT_ID_COLUMN]))

# %%
import qgrid

#qgrid.show_grid(dfs['ATW-hflip.mp4'][MatchLevel.LEVEL_A])
#qgrid.show_grid(grouped_by_name_pairs.get_group(('5c5714c0a56fd2a96f99db2f59b0d03659d77cdf.flv', '6d1a89c83d554fc6a5e39fcadb172a79baf140fd.mp4')))
#qgrid.show_grid(awesome_matches)

# %%
