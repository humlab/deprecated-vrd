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
# # Tool: Fingerprint Extractor
#
# Explore the fingerprints for a single video
#
# We begin by some necessary boilerplate for accessing the files,

# %%
from notebook_util import video_selector
from IPython.display import display

video_selection = video_selector()
display(video_selection)

# %%
print(f'Selected video {video_selection.value}')

# %%
from IPython.display import Video
from pathlib import Path
from notebook_util import display_video

display_video('/home/jovyan/work/' + video_selection.value)

# %% [markdown]
# And then, we compute the fingerprints for the video,

# %%
from video_reuse_detector.fingerprint import extract_fingerprint_collection_with_keyframes
from pathlib import Path
import os

INTERIM_DIRECTORY = Path(os.environ['INTERIM_DIRECTORY'])
video_path = Path(video_selection.value)

# Map from segment id to tuples of the type (Keyframe, FingerprintCollection)
segment_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(video_path, INTERIM_DIRECTORY)
print(f'Done extracting fingerprints for "{video_path.name}"')

print('Done extracting fingerprints!')

# %%
from video_reuse_detector.ffmpeg import get_video_duration
print(get_video_duration(video_path))

# %%
from video_reuse_detector.fingerprint import segment_id_keyframe_fp_map_to_list
from video_reuse_detector.fingerprint import FingerprintComparison

fingerprints = segment_id_keyframe_fp_map_to_list(segment_id_to_keyframe_fps_map)

# %%
from notebook_util import plot_keyframe, plot_color_correlation, rgb
import cv2

def plot_fingerprints(
    fps_w_keyframes, 
    input_offset, 
    no_of_fps_on_display=5):
    from matplotlib import pyplot as plt
    from matplotlib.image import imread

    total_no_of_fps = len(fps_w_keyframes.keys())

    # 1) Keyframe
    # 2) Color Correlation
    fig, axs = plt.subplots(2, no_of_fps_on_display)
    
    offset = input_offset
    # Ensure that the offsets are in range
    if offset + no_of_fps_on_display >= total_no_of_fps:
        offset = total_no_of_fps - no_of_fps_on_display
        
    for i in range(no_of_fps_on_display):
        keyframe, fingerprint = fps_w_keyframes[offset+i]
        
        orb = fingerprint.orb
        
        if orb:
            img  = cv2.drawKeypoints(keyframe.image, orb.keypoints, None, color=(0, 255, 0), flags=0)
            axs[0][i].imshow(rgb(img))
        else:
            plot_keyframe(axs[0][i], keyframe)
            
        plot_color_correlation(axs[1][i], fingerprint.color_correlation)    
        plt.axis('off')

    plt.show()
    
    
from ipywidgets import IntSlider
from ipywidgets import interact

no_of_frames = len(segment_id_to_keyframe_fps_map.keys())
offset_widget = IntSlider(min=0, max=no_of_frames-1)

interact(lambda x: plot_fingerprints(segment_id_to_keyframe_fps_map, 
                                     x), 
         x=offset_widget)

# %%
