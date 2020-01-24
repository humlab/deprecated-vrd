# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Comparing Fingerprints
#
# In this notebook we begin by looking at two videos, wherein one is a perturbed version of the other. Afterwards, we will fingerprint the two videos in their entirety, before ultimately comparing all the resulting video fingerprints. We'll have a precursory look at the fingerprints that signal a high degree of similarity.
#
# We begin by some necessary boilerplate for accessing the files,

# %%
import os
from pathlib import Path

video_directory = Path(os.environ['VIDEO_DIRECTORY'])

# %% [markdown]
# And then have a look at our reference video,

# %%
from IPython.display import Video

reference_video_name = 'panorama_augusti_1944_000030_000040_10s.mp4'

reference_video_path = video_directory / reference_video_name
assert(reference_video_path.exists())

# Video expects a relative path in relation to the notebook
rel_path = reference_video_path.relative_to(Path.cwd())
Video(str(rel_path))

# %% [markdown]
# And likewise for our query video,

# %%
from IPython.display import Video

query_video_name = 'panorama_augusti_1944_000030_000040_10s_blur_luma_radius_5_chroma_radius_10_luma_power_1.mp4'

query_video_path = video_directory / query_video_name
assert(query_video_path.exists())

rel_path = query_video_path.relative_to(Path.cwd())
Video(str(rel_path))

# %% [markdown]
# And then, we compute the fingerprints for each respective video,

# %%
from video_reuse_detector.fingerprint import extract_fingerprint_collection_with_keyframes

# Extracting fingerprints produces artefacts that are written to disk
root_output_directory = Path.cwd() / 'notebooks/interim/'

# Map from segment id to tuples of the type (Keyframe, FingerprintCollection)
query_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(query_video_path, root_output_directory)
reference_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(reference_video_path, root_output_directory)

# Extract only the fingerprints
query_fps = dict(query_id_to_keyframe_fps_map.values()).values()
reference_fps = dict(reference_id_to_keyframe_fps_map.values()).values()

# %% [markdown]
# Now, `query_fps` and `reference_fps` are lists of fingerprints such that each element in the list is a fingerprint for a segment of the input video. To compare them, we use `FingerprintComparison.compare_all`, which yields a mapping from the segment ids in the query video to a list of segment ids in the reference videos that is sorted based on how similar the two segments are,

# %%
from video_reuse_detector.fingerprint import FingerprintComparison

sorted_comparisons = FingerprintComparison.compare_all(query_fps, reference_fps)

# %% [markdown]
# This means that `sorted_comparisons[0]` is a list that is equal in length to the number of segments in the reference video, and that the first element therein is the segment in the reference video most similar to the first segment in the query video.
#
# > `sorted_comparisons[0][0]` is the segment in our reference video most like the first segment in our query video. 
#
# For each element in `sorted_comparisons[n]` the attribute `similarity_score` is a percentage indicating how similar the segment pair is. We find that the segment most similar to the first segment in our query video happens to be the second segment in our reference video, as per the following assertion,

# %%
assert(sorted_comparisons[0][0].reference_segment_id == 1)

# %% [markdown]
# And that they are more than 95% similar,

# %%
assert(sorted_comparisons[0][0].similarity_score > 0.95)
sorted_comparisons[0][0].similarity_score

# %% [markdown]
# Their `match_level` indicates on what aspects they have been deemed to be similar. The high percentage betrays that their `match_level` will be `MatchLevel.LEVEL_A`, as confirmed below

# %%
from video_reuse_detector.fingerprint import MatchLevel
assert(sorted_comparisons[0][0].match_level == MatchLevel.LEVEL_A)

# %% [markdown]
# This means that their thumbnails were similar, they had the same color information, and their ORB-decriptors were comparable.
#
# First, we look at the respective keyframes,

# %%
# %matplotlib inline
from matplotlib import pyplot as plt
from notebook_util import rgb

fig = plt.figure()

query_keyframe, query_fingerprint = query_id_to_keyframe_fps_map[0]
assert(query_fingerprint.segment_id == 0)

ax = fig.add_subplot(121);
ax.imshow(rgb(query_keyframe.image))

reference_keyframe, reference_fingerprint = reference_id_to_keyframe_fps_map[0]
assert(reference_fingerprint.segment_id == 0)

ax = fig.add_subplot(122);
ax.imshow(rgb(reference_keyframe.image));

plt.show()

# %% [markdown]
# Their cc,

# %%
import numpy as np
from video_reuse_detector.color_correlation import ColorCorrelation, CORRELATION_CASES

query_cc = query_fingerprint.color_correlation
reference_cc = reference_fingerprint.color_correlation

indices = np.arange(len(CORRELATION_CASES))

plt.ylabel('Percent')
plt.xlabel('Correlation Case')

plt.bar(indices, list(query_cc.histogram.values()), color="orangered", alpha=0.5)
plt.bar(indices, list(reference_cc.histogram.values()), color='mediumslateblue', alpha=0.5)

plt.xticks(indices, CORRELATION_CASES)
plt.show()



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

plt.subplot(121); plt.imshow(img1)
plt.subplot(122); plt.imshow(img2)

plt.show()

# %%
