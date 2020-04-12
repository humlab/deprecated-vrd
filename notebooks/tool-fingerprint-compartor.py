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
# # Tool: Fingerprint Comparator
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
from pathlib import Path
from notebook_util import display_video

display_video('/home/jovyan/work/' + query_video_selection.value)

# %%
display_video('/home/jovyan/work/' + reference_video_selection.value)

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
from video_reuse_detector.ffmpeg import get_video_duration
print(get_video_duration(query_video_path))
print(get_video_duration(reference_video_path))

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
from notebook_util import plot_keyframe, plot_stacked_color_correlation, rgb
import cv2

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
        query_keyframe, query_fingerprint = query_fps_w_keyframes[query_offset+i]
        #plot_keyframe(axs[0][i], keyframe)
        
        reference_keyframe, reference_fingerprint = reference_fps_w_keyframes[reference_offset+i]
        #plot_keyframe(axs[1][i], keyframe)

        query_orb = query_fingerprint.orb
        reference_orb = reference_fingerprint.orb
        
        if query_orb:
            query_img  = cv2.drawKeypoints(query_keyframe.image, query_orb.keypoints, None, color=(0, 255, 0), flags=0)
            axs[0][i].imshow(rgb(query_img))
        else:
            plot_keyframe(axs[0][i], query_keyframe)
            
        if reference_orb:
            reference_img = cv2.drawKeypoints(reference_keyframe.image, reference_orb.keypoints, None, color=(0, 255, 0), flags=0)
            axs[1][i].imshow(rgb(reference_img))
        else:
            plot_keyframe(axs[1][i], reference_keyframe)
        
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

# %%
