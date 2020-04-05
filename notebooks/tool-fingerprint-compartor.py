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

# %% [markdown]
# # Comparing a Video Against Horizontal Flip
#
# In this notebook we compare a video against itself after it has been flipped horizontally.
#
# We begin by some necessary boilerplate for accessing the files,

# %%
from notebook_util import video_selector

query_video_selection = video_selector()

# %%
query_video_selection

# %%
reference_video_selection = video_selector()

# %%
reference_video_selection

# %%
print(f'Selected query video {query_video_selection.value}')
print(f'Selected reference video {reference_video_selection.value}')

# %%
from IPython.display import Video

Video(query_video_selection.value)

# %%
Video(reference_video_selection.value)

# %% [markdown]
# And then, we compute the fingerprints for each respective video,

# %%
from video_reuse_detector.fingerprint import extract_fingerprint_collection_with_keyframes
from pathlib import Path
import os

INTERIM_DIRECTORY = Path(os.environ['INTERIM_DIRECTORY'])
query_video_path = Path(query_video_selection.value)
reference_video_path = Path(reference_video_selection.value)

# Map from segment id to tuples of the type (Keyframe, FingerprintCollection)
query_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(query_video_path, INTERIM_DIRECTORY)
print(f'Done extracting fingerprints for "{query_video_path.name}"')
reference_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(reference_video_path, INTERIM_DIRECTORY)
print(f'Done extracting fingerprints for "{reference_video_path.name}"')

print('Done extracting fingerprints!')

# %%
"""
%matplotlib inline
from ipywidgets import interactive

# TODO: Migrate to common utilities/"recipe"
def plot_keyframes(id_to_keyframe_fingerprint_collection_map, input_offset, no_of_frames_on_display=5):
    from matplotlib import pyplot as plt
    from matplotlib.image import imread

    total_no_of_frames = len(id_to_keyframe_fingerprint_collection_map.keys())
    fig, axs = plt.subplots(1, no_of_frames_on_display)
    
    offset = input_offset
    if input_offset + no_of_frames_on_display >= total_no_of_frames:
        offset = total_no_of_frames - no_of_frames_on_display
    
    for i in range(no_of_frames_on_display):
        keyframe, _ = id_to_keyframe_fingerprint_collection_map[offset+i]
        axs[i].imshow(keyframe.image)
        axs[i].axis('off')

    plt.show()
    
query_no_of_frames = len(query_id_to_keyframe_fps_map.keys())
interactive(lambda offset: plot_keyframes(query_id_to_keyframe_fps_map, offset), 
            offset=(0, query_no_of_frames-1))
            
reference_no_of_frames = len(reference_id_to_keyframe_fps_map.keys())
interactive(lambda offset: plot_keyframes(reference_id_to_keyframe_fps_map, offset), 
            offset=(0, reference_no_of_frames-1))
"""

# %%
from video_reuse_detector.fingerprint import segment_id_keyframe_fp_map_to_list
from video_reuse_detector.fingerprint import FingerprintComparison

query_fps = segment_id_keyframe_fp_map_to_list(query_id_to_keyframe_fps_map)
reference_fps = segment_id_keyframe_fp_map_to_list(reference_id_to_keyframe_fps_map)

print('Comparing fingerprints...')
sorted_comparisons = FingerprintComparison.compare_all(query_fps, reference_fps)
print('Comparisons complete!')

# %%
# Take the sorted comparisons and create a mapping d[query_segment_id][reference_segment_id]
comparisons_sorted_by_segment_id = {}
for query_segment_id, comparisons in sorted_comparisons.items():
    reference_segment_id = lambda comparison: comparison.reference_segment_id
    
    comparisons_sorted_by_segment_id[query_segment_id] = sorted(
        sorted_comparisons[query_segment_id], key=reference_segment_id
    )
    
for i in range(len(comparisons_sorted_by_segment_id.keys())):
    comparisons = comparisons_sorted_by_segment_id[i]
    for j in range(len(comparisons)):
        assert(comparisons_sorted_by_segment_id[i][j].query_segment_id == i)
        assert(comparisons_sorted_by_segment_id[i][j].reference_segment_id == j)

# %%
from notebook_util import plot_keyframe, plot_stacked_color_correlation, text

def plot_fingerprints(
    query_fps_w_keyframes, 
    reference_fps_w_keyframes,
    comparisons_sorted_by_segment_id,
    query_input_offset, 
    reference_input_offset, 
    no_of_fps_on_display=5):
    from matplotlib import pyplot as plt
    from matplotlib.image import imread

    query_total_no_of_fps = len(query_fps_w_keyframes.keys())
    reference_total_no_of_fps = len(reference_fps_w_keyframes.keys())

    # 1. Query keyframes with ORB
    # 2. Reference keyframes with ORB
    # 3. TODO: Query thumbnail
    # 4. TODO: Reference thumbnail
    # 5 (3). CC overlay between both videos
    # 6 (4). Text data
    fig, axs = plt.subplots(4, no_of_fps_on_display)
    
    query_offset = query_input_offset
    # Ensure that the offsets are in range
    if query_input_offset + no_of_fps_on_display >= query_total_no_of_fps:
        query_offset = query_total_no_of_fps - no_of_fps_on_display
        
    reference_offset = reference_input_offset
    # Ensure that the offsets are in range
    if reference_input_offset + no_of_fps_on_display >= reference_total_no_of_fps:
        reference_offset = reference_total_no_of_fps - no_of_fps_on_display
        
    comparisons = comparisons_sorted_by_segment_id

    for i in range(no_of_fps_on_display):
        keyframe, query_fingerprint = query_fps_w_keyframes[query_offset+i]
        plot_keyframe(axs[0][i], keyframe)
        
        keyframe, reference_fingerprint = reference_fps_w_keyframes[reference_offset+i]
        plot_keyframe(axs[1][i], keyframe)
        
        plot_stacked_color_correlation(axs[2][i], query_fingerprint, reference_fingerprint)
        
        comparison = comparisons[query_offset+i][reference_offset+i]
        query_segment_id = comparison.query_segment_id
        reference_segment_id = comparison.reference_segment_id
        
        text_data = '\n'.join([
            f'Q_id: {query_segment_id}',
            f'R_id: {reference_segment_id}',
            f'{comparison.match_level.name}',
            f' th: {comparison.similar_enough_th}',
            f' cc: {comparison.could_compare_cc and comparison.similar_enough_cc}',
            f' orb: {comparison.could_compare_orb and comparison.similar_enough_orb}',
            f'{10*comparison.similarity_score:.3f}'
        ])
        
        axs[3][i].text(0, -1.5, text_data)
        plt.sca(axs[3][i])
        plt.axis('off')

    plt.show()
    
    
from ipywidgets import IntSlider
from ipywidgets import interact

query_no_of_frames = len(query_id_to_keyframe_fps_map.keys())
query_widget = IntSlider(min=0, max=query_no_of_frames-1)

reference_no_of_frames = len(reference_id_to_keyframe_fps_map.keys())
reference_widget = IntSlider(min=0, max=reference_no_of_frames-1)

interact(lambda x, y: plot_fingerprints(query_id_to_keyframe_fps_map, 
                                        reference_id_to_keyframe_fps_map,
                                        comparisons_sorted_by_segment_id,
                                        x, 
                                        y), 
         x=query_widget, y=reference_widget)

# %% [markdown]
# We extract the fingerprints by themselves, please refer to 2.0-fingerprint-comparison.py if the following steps are unclear,

# %%
query_fps = dict(query_id_to_keyframe_fps_map.values()).values()
reference_fps = dict(reference_id_to_keyframe_fps_map.values()).values()

# %%
from video_reuse_detector.fingerprint import FingerprintComparison

sorted_comparisons = FingerprintComparison.compare_all(query_fps, reference_fps)


# %%
def best_match(sorted_comparisons, query_segment_id):
    # Get the best FingerprintComparison for the given query video segment id
    return sorted_comparisons[query_segment_id][0]


# %%
best_matches_by_segment = {}

for segment_id in sorted_comparisons.keys():  # For every n as it were
    # Fetch the best match
    best_match_for_segment = best_match(sorted_comparisons, segment_id)
    
    # Collect it
    best_matches_by_segment[segment_id] = best_match_for_segment

# %% [markdown]
# The `match_level` between two segments indicate on what aspects they have been deemed to be similar. A `MathLevel.A` means that for the segment pair their thumbnails were similar, they had the same color information, and their ORB-decriptors were comparable. Another thing that can be inferred is that their `similarity_score` will be high.
#
# Again recall that `best_matches[n]` is the best match that exists for the `n`th segment in the query reference video. As per the above, we'd find the best matches overall by filtering for the elements with `match_level == MatchLevel.LEVEL_A`.

# %%
# %matplotlib inline
from video_reuse_detector.fingerprint import MatchLevel
from matplotlib import pyplot as plt
import numpy as np

def filter_comparisons_by_level(matches, level):
    return list(filter(lambda fc: fc.match_level == level, matches))

absolute_best_matches = filter_comparisons_by_level(best_matches_by_segment.values(), MatchLevel.LEVEL_A)
similarity_scores = [match.similarity_score for match in absolute_best_matches]
query_segment_ids = [match.query_segment_id for match in absolute_best_matches]

indices = np.arange(len(similarity_scores))
plt.bar(indices, similarity_scores)
plt.xlabel('Query Segment Id')
plt.ylabel('Percentage')
plt.xticks(indices, query_segment_ids)
plt.title('Similarity Scores for Matches with MatchLevel.LEVEL_A')
plt.show()

# %% [markdown]
# This time we do not expect all the similarity scores to be 1.0, but very close to it,

# %%
print(f'similarity_scores={similarity_scores}')
assert(all([score >= 0.9999 for score in similarity_scores]))

# %% [markdown]
# As a case-study we take one of these comparisons and look at the artefacts that compose the reference and query fingerprint.

# %%
fingerprint_comparison = absolute_best_matches[0]
query_segment_id = fingerprint_comparison.query_segment_id
reference_segment_id = fingerprint_comparison.reference_segment_id

# %% [markdown]
# First, we look at the respective keyframes,

# %%
from notebook_util import rgb

fig = plt.figure()

query_keyframe, query_fingerprint = query_id_to_keyframe_fps_map[query_segment_id]
assert(query_fingerprint.segment_id == query_segment_id)

ax = fig.add_subplot(121);
ax.imshow(rgb(query_keyframe.image))

reference_keyframe, reference_fingerprint = reference_id_to_keyframe_fps_map[reference_segment_id]
assert(reference_fingerprint.segment_id == reference_segment_id)

ax = fig.add_subplot(122);
ax.imshow(rgb(reference_keyframe.image));

plt.show()

# %% [markdown]
# Rendering their color correlation by stacking the histogram bins on top of one another should yield no stacked bars, refer to 2.0-fingerprint-comparison.py for an example of what that looks like,

# %%
from skimage.feature import (match_descriptors, plot_matches)
import cv2

orb1 = reference_fingerprint.orb
orb2 = query_fingerprint.orb
descriptors1 = orb1.descriptors
descriptors2 = orb2.descriptors
keypoints1 = orb1.keypoints
keypoints2 = orb2.keypoints
matches12 = match_descriptors(descriptors1, descriptors2, cross_check=True)

img1 = cv2.drawKeypoints(reference_keyframe.image, orb1.keypoints, None, color=(0, 255, 0), flags=0)
img2 = cv2.drawKeypoints(query_keyframe.image, orb2.keypoints, None, color=(0, 255, 0), flags=0)

plt.subplot(121); plt.imshow(rgb(img1))
plt.subplot(122); plt.imshow(rgb(img2))

plt.show()
