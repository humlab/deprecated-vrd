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
# # Fingerprinting Overview
#
# A short rundown of the fingerprinting process.

# %% [markdown]
# ## 1. Extracting & Downsampling Video Segments
#
# The first step in the fingerprinting process is to divide a video into shorter video sequences that are all of equal length (best-effort). These "sub-videos" will be referred to as "segments". These segments are extracted in sequence from the start of the input film without any overlap. 
#
# To segment a video, a `Path`-instance to the video is required,

# %%
import os
from pathlib import Path
from notebook_util import video_selector

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])
video_selection = video_selector(default=str(VIDEO_DIRECTORY / 'panorama_augusti_1944.mp4'))
display(video_selection)

# %% [markdown]
# To make the output of the remaining steps easy to grasp we extract a slice of the input video

# %%
import video_reuse_detector.ffmpeg as ffmpeg

input_file = Path(video_selection.value)

assert(input_file.exists())

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
input_file = ffmpeg.slice(input_file, "00:00:30", "00:00:10", OUTPUT_DIRECTORY)
assert(input_file.exists())

# %% [markdown]
# And in-case something goes wrong, we output some information about the input file to make debugging/error-reporting easy,

# %%
from video_reuse_detector.ffmpeg import get_video_duration, get_video_dimensions
import math

video_duration = get_video_duration(input_file)
print(video_duration)
print(get_video_dimensions(input_file))

# %% [markdown]
# The extracted video segments are downsampled by extracting individual frames from it, 

# %%
from video_reuse_detector.downsample import downsample
from video_reuse_detector.fingerprint import chunks

fps = 5
paths_to_extracted_frames = list(chunks(downsample(input_file, OUTPUT_DIRECTORY, fps=fps), chunk_size=fps))
no_of_chunks = len(paths_to_extracted_frames)

print(f'Extracted n={no_of_chunks} chunks')
print(f'All chunks are of length={fps}')

no_of_frames_per_chunk = fps
assert(all(len(chunk) == no_of_frames_per_chunk for chunk in paths_to_extracted_frames))


# %% [markdown]
# For every given second in the input to `downsample` an `fps` number of frames are extracted. The extracted frames are uniformly distributed across each second of video.
#
# The resulting extracted frames are shown below,

# %%
# %matplotlib inline

from matplotlib import pyplot as plt
from matplotlib.image import imread

fig, axs = plt.subplots(no_of_chunks, no_of_frames_per_chunk)

for i in range(no_of_chunks):
    for j in range(no_of_frames_per_chunk):
        axs[i][j].imshow(imread(paths_to_extracted_frames[i][j]))
        axs[i][j].axis('off')

plt.show()

# %% [markdown]
# ## 3. Producing keyframes
#
# The extracted frames in the previous step are aggregated together on a chunk-per-chunk basis by
#
# 1. Overlaying them on top of one another,
# 2. scaling the resulting image up slightly, and
# 3. cropping the upscaled image with a central alignment.
#
# The purpose of these operations is to,
#
# 1. Withstand video attacks that perturb the playback speed of the original video, and 
# 2. center our keyframe on what is heuristically the most pertinent information in the video material.
#
# To elaborate on the second item, generally the subject matter of a film tends to be toward the center of the frame whereas the content at the edges is not as significant.

# %%
from video_reuse_detector.keyframe import Keyframe
from notebook_util import rgb

fig, axs = plt.subplots(no_of_chunks, 1)

keyframes = []

for i in range(no_of_chunks):
    keyframe = Keyframe.from_frame_paths(paths_to_extracted_frames[i])
    keyframes.append(keyframe)
    axs[i].imshow(rgb(keyframe.image))
    axs[i].axis('off')

plt.show()

# %% [markdown]
# ## 4. Producing a thumbnail
#
# The first artefact that constitutes the fingerprint of a video segment is its thumbnail representation. The thumbnail representation for a video segment is produced by mirroring the keyframe image around its horizontal center, and discarding its color information. If two thumbnails are similar, it means that the visual component of the video segments are similar enough to compare other parts of the fingerprint, such as its color make-up and the objects shown in the frame.
#
# When comparing the fingerprints of two video segments, the thumbnail is the first characteristic that is compared, to quickly determine if two keyframes are remotely similar.
#
# Looking at a thumbnail, we find that it is not readily discernable to us humans what operations went into producing it, so before we construct an _actual_ thumbnail, let us apply the same transformations to our keyframe image _first_ without changing the size of the image as to adequately convey what is happening.
#
# Thumbnails are created through three operations,
#
# 1. Blockwise reducing the image into a normalized grayscale representation,
# 2. Folding the image over the horizontal axis
# 3. Downsizing the image to `30x30`-pixels
#
# The third operation is self-explanatory, and need not be explored. However, we will perform the first and second operation as stand-alone operations. I.e., we will use the original keyframe image as the input to both transformations while in reality the second operation is applied to the result of the first. This is because the first operation, as we'll see, discards a lot of visual information and thus the effect of the second operation is less comprehensible than it'll be when applied to a "regular" image.
#
# ### 4.1 Blockwise reduction to a normalized grayscale representation

# %%
import video_reuse_detector.image_transformation as image_transformation

# We'll use the first keyframe as an example here,
keyframe = keyframes[0]

gs = image_transformation.normalized_grayscale(keyframe.image, no_of_blocks=4)
plt.imshow(gs, cmap='gray')
plt.show()

# %% [markdown]
# ### 4.2 Image folding

# %%
import video_reuse_detector.image_transformation as image_transformation

folded = image_transformation.fold(keyframe.image)
plt.imshow(rgb(folded))
plt.show()

# %%
fig = plt.figure()

ax = fig.add_subplot(121);
ax.imshow(rgb(folded))
ax = fig.add_subplot(122);
ax.imshow(rgb(folded));
ax.axvline(keyframe.image.shape[1]/2, color='r')

plt.show()

# %% [markdown]
# ### 4.3 Genuine thumbnail production

# %%
from video_reuse_detector.thumbnail import Thumbnail

thumbnail = Thumbnail.from_image(keyframe.image)

plt.imshow(rgb(thumbnail.image))
plt.show()

# %% [markdown]
# ## 5. Extracting Color Correlation

# %% [markdown]
# To fingerprint the color information of a video segment its keyframe is blockwise reduced into the average color of each respective block, i.e., for our keyframe image from before,

# %%
plt.imshow(rgb(keyframe.image))
plt.show()

# %% [markdown]
# We decompose the image into 16 blocks,

# %%
import matplotlib.ticker as plticker
from video_reuse_detector.util import compute_block_size

# Set up figure
fig = plt.figure()
ax = fig.add_subplot(111)

# Remove whitespace from around the image
fig.subplots_adjust(left=0,right=1,bottom=0,top=1)
block_height, block_width = compute_block_size(keyframe.image, nr_of_blocks=16)

# Set the gridding interval: here we use the major tick interval
ax.xaxis.set_major_locator(plticker.MultipleLocator(base=block_width))
ax.yaxis.set_major_locator(plticker.MultipleLocator(base=block_height))

# Add the grid
ax.grid(which='major', axis='both', linestyle='-', color='r')

# Add the image
ax.imshow(rgb(keyframe.image))
plt.show()

# %% [markdown]
# And then the color average from each block is computed, so for instance, the top-left block looks as follows

# %%
top_left_block = keyframe.image[0:block_height, 0:block_width, :]
plt.imshow(rgb(top_left_block))
plt.show()

# %%
from video_reuse_detector.color_correlation import avg_intensity_per_color_channel

average_color_top_left_block = avg_intensity_per_color_channel(top_left_block)
average_color_top_left_block

# %% [markdown]
# Please confirm visually,

# %%
plt.axes()

def fc(bgr_tuple):
    b, g, r = bgr_tuple
    return tuple(color/255 for color in (r, g, b))

square = plt.Rectangle((10, 10), 100, 100, fc=fc(average_color_top_left_block))
plt.gca().add_patch(square)

plt.axis('scaled')
plt.axis('off')
plt.show()

# %% [markdown]
# And on an image level, the blockwise color reduction yields the following,

# %%
import numpy as np
from video_reuse_detector.color_correlation import color_transformation_and_block_splitting

averages = color_transformation_and_block_splitting(keyframe.image)
plt.subplot(121); plt.imshow(rgb(keyframe.image))
plt.subplot(122); plt.imshow(rgb(averages.astype(np.uint8)))

assert(np.array_equal(averages[0, 0, :], average_color_top_left_block))

plt.show()

# %%
from video_reuse_detector.color_correlation import ColorCorrelation, CORRELATION_CASES

color_correlation = ColorCorrelation.from_image(keyframe.image)
indices = np.arange(len(CORRELATION_CASES))
plt.bar(indices, color_correlation.histogram.values())
plt.ylabel('Percent')
plt.xlabel('Correlation Case')
plt.xticks(indices, CORRELATION_CASES)
plt.show()

# %% [markdown]
# ## 5. ORB

# %%
from video_reuse_detector.orb import ORB
import cv2

orb = ORB.from_image(keyframe.image)

img = cv2.drawKeypoints(keyframe.image, orb.keypoints, None, color=(0, 255, 0), flags=0)

plt.imshow(rgb(img))
plt.show()
