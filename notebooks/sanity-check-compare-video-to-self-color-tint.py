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
# # Comparing a Video Against Itself After Tint
#
# In this notebook we compare a video against itself.
#
# We begin by some necessary boilerplate for accessing the files,

# %%
import os
from pathlib import Path

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])
assert(VIDEO_DIRECTORY.exists())
print(f'VIDEO_DIRECTORY={VIDEO_DIRECTORY}')

# %% [markdown]
# And then have a look at our reference video,

# %%
from IPython.display import Video
import video_reuse_detector.ffmpeg as ffmpeg

reference_video_path = VIDEO_DIRECTORY / 'ATW-644.mp4'
assert(reference_video_path.exists())

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
reference_video_path = ffmpeg.slice(reference_video_path, "00:00:30", "00:00:05", OUTPUT_DIRECTORY)
assert(reference_video_path.exists())
print(f'reference_video_path={reference_video_path}')

# Video expects a relative path in relation to the notebook
rel_path = reference_video_path.relative_to(Path.cwd())
Video(str(rel_path))

# %% [markdown]
# And use the same video as our query video,

# %%
query_video_path = ffmpeg.tint(reference_video_path, OUTPUT_DIRECTORY)
assert(query_video_path.exists())
print(f'query_video_path={query_video_path}')
Video(str(query_video_path.relative_to(Path.cwd())))

# %% [markdown]
# And then, we compute the fingerprints for each respective video,

# %%
from video_reuse_detector.fingerprint import extract_fingerprint_collection_with_keyframes

INTERIM_DIRECTORY = Path(os.environ['INTERIM_DIRECTORY'])

# Map from segment id to tuples of the type (Keyframe, FingerprintCollection)
query_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(query_video_path, INTERIM_DIRECTORY)
reference_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(reference_video_path, INTERIM_DIRECTORY)

# %% [markdown]
# We observe the resulting keyframes and expect them to be **equal** but different in color,

# %%
# %matplotlib inline

from notebook_util import rgb

def plot_keyframes(id_to_keyframe_fingerprint_collection_map):
    from matplotlib import pyplot as plt
    from matplotlib.image import imread

    no_of_frames = len(id_to_keyframe_fingerprint_collection_map.keys())
    fig, axs = plt.subplots(1, no_of_frames)

    for i in range(no_of_frames):
        keyframe, _ = id_to_keyframe_fingerprint_collection_map[i]
        axs[i].imshow(rgb(keyframe.image))
        axs[i].axis('off')

    plt.show()
    
plot_keyframes(reference_id_to_keyframe_fps_map)
plot_keyframes(query_id_to_keyframe_fps_map)

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
# The similarity scores for these segments should all be fairly high

# %%
print(f'similarity_scores={similarity_scores}')
assert(all([score > 0.9 for score in similarity_scores]))

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

# %% [markdown]
# Ultimately we render out the ORB-descriptors. Expect these to be **equal**

# %%
import cv2

orb1 = reference_fingerprint.orb
orb2 = query_fingerprint.orb
descriptors1 = orb1.descriptors
descriptors2 = orb2.descriptors
keypoints1 = orb1.keypoints
keypoints2 = orb2.keypoints

img1 = cv2.drawKeypoints(reference_keyframe.image, orb1.keypoints, None, color=(0, 255, 0), flags=0)
img2 = cv2.drawKeypoints(query_keyframe.image, orb2.keypoints, None, color=(0, 255, 0), flags=0)

plt.subplot(121); plt.imshow(rgb(img1))
plt.subplot(122); plt.imshow(rgb(img2))

plt.show()

# %%
