# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.4
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

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])

# %% [markdown]
# And then have a look at our reference video,

# %%
from IPython.display import Video
import video_reuse_detector.ffmpeg as ffmpeg

reference_video_path = VIDEO_DIRECTORY / 'panorama_augusti_1944.mp4'
assert(reference_video_path.exists())

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
reference_video_path = ffmpeg.slice(reference_video_path, "00:01:30", "00:00:10", OUTPUT_DIRECTORY)
assert(reference_video_path.exists())

# Video expects a relative path in relation to the notebook
rel_path = reference_video_path.relative_to(Path.cwd())
Video(str(rel_path))

# %% [markdown]
# And likewise for our query video,

# %%
from IPython.display import Video

query_video_path = ffmpeg.blur(reference_video_path, OUTPUT_DIRECTORY)
assert(query_video_path.exists())

rel_path = query_video_path.relative_to(Path.cwd())
Video(str(rel_path))

# %% [markdown]
# And then, we compute the fingerprints for each respective video,

# %%
from video_reuse_detector.fingerprint import extract_fingerprint_collection_with_keyframes

INTERIM_DIRECTORY = Path(os.environ['INTERIM_DIRECTORY'])

# Map from segment id to tuples of the type (Keyframe, FingerprintCollection)
query_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(query_video_path, INTERIM_DIRECTORY)
reference_id_to_keyframe_fps_map = extract_fingerprint_collection_with_keyframes(reference_video_path, INTERIM_DIRECTORY)

# Extract only the fingerprints
query_fps = dict(query_id_to_keyframe_fps_map.values()).values()
reference_fps = dict(reference_id_to_keyframe_fps_map.values()).values()

# %% [markdown]
# Now, `query_fps` and `reference_fps` are lists of fingerprints such that each element in the list is a fingerprint for a segment of the input video. To compare them, we use `FingerprintComparison.compare_all`, which yields a mapping from the segment ids in the query video to a list of segment ids in the reference videos that is sorted based on how similar the two segments are,

# %%
from video_reuse_detector.fingerprint import FingerprintComparison

sorted_comparisons = FingerprintComparison.compare_all(query_fps, reference_fps)


# %% [markdown]
# If the query video is `S` seconds long, then for any non-negative `n` less than `S` we have that `sorted_comparisons[n]` is a list of `FingerprintComparison`-objects wherein the first element in the list is the `FingerprintComparison`-object that describes the best match in relation to the query video segment related to `n`.
# For any `n` this list is equal in length to the number of segments in the reference video.
#
# Take-away:
#
# > `sorted_comparisons[0][0]` is the segment in our reference video most like the first segment in our query video. 
#
# Thus, we formulate

# %%
def best_match(sorted_comparisons, query_segment_id):
    # Get the best FingerprintComparison for the given query video segment id
    return sorted_comparisons[query_segment_id][0]


# %% [markdown]
# For each element in `sorted_comparisons[n]` the attribute `similarity_score` is a percentage indicating how similar the segment pair is. 
#
# For the first query video segment, we have that the best match is reference segment with id=0

# %%
assert(best_match(sorted_comparisons, 0).reference_segment_id == 0)
best_match(sorted_comparisons, 0).reference_segment_id

# %% [markdown]
# And that they are more than 70% similar,

# %%
assert(best_match(sorted_comparisons, 0).similarity_score > 0.70)
sorted_comparisons[0][0].similarity_score

# %% [markdown]
# Now, while this is the best match for the first segment in the query video this does _not_ mean that it is the best match we have between any two pairs of video segments.
#
# To find the best matches available to us, we recall that 
#
# > `sorted_comparisons[n][0]` is the segment in our reference video most like the nth segment in our query video. 
#
# Thus, for every `n` we simply collect these items.

# %%
best_matches_by_segment = {}

for segment_id in sorted_comparisons.keys():  # For every n as it were
    # Fetch the best match
    best_match_for_segment = best_match(sorted_comparisons, segment_id)
    
    # Collect it
    best_matches_by_segment[segment_id] = best_match_for_segment

# %% [markdown]
# We have that these matches are objects of the type `FingerprintComparison`

# %%
from video_reuse_detector.fingerprint import FingerprintComparison

assert(all(type(fc) == FingerprintComparison for fc in best_matches_by_segment.values()))

# %% [markdown]
# That in turn is composed of the following attributes,

# %%
FingerprintComparison.__dataclass_fields__.keys()

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
plt.xlabel('Segment id')
plt.ylabel('Percentage')
plt.xticks(indices, query_segment_ids)
plt.title('Similarity Scores for Matches with MatchLevel.LEVEL_A')
plt.show()

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
# Their cc,

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
