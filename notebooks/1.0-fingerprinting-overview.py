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
# # Fingerprinting Overview
#
# A short rundown of the fingerprinting process.

# %% [markdown]
# ## 1. Extracting video segments
#
# The first step in the fingerprinting process is to divide a video into chunks of equal length. These chunks are referred to as "video segments" or, for short, "segments". Segments are extracted without overlap, and the segments are independently fingerprinted.
#
# To segment a video, a `Path`-instance to the video is required,

# %%
import os
from pathlib import Path
import video_reuse_detector.ffmpeg as ffmpeg

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])
input_file = VIDEO_DIRECTORY / 'panorama_augusti_1944.mp4'
assert(input_file.exists())

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
input_file = ffmpeg.slice(input_file, "00:00:30", "00:00:05", OUTPUT_DIRECTORY)
assert(input_file.exists())

# %% [markdown]
# Afterwards, invoking `video_reuse_detector.segment` on the file will split it into segments. Under the hood, `ffmpeg` is leveraged to split the given video into a new set of shorter videos wherein each video is a extracted portion of the original. 

# %%
from video_reuse_detector.segment import segment

# The segments produced by the function need to be written to disk
segment_file_paths = segment(input_file, OUTPUT_DIRECTORY / input_file.stem)

# %% [markdown]
# By default, a video that is `S` seconds long is divided into `S` number of segments, meaning that in the default case each second of a given video is treated as its own segment. The length of a video segment is parameterised, and it is possible to produce fingerprints using segments that are _longer_ than this, which trades accuracy with regards to determining video reuse against the speed at which fingerprints can be computed.
#
# In the above code-block the function was invoked using its default parameters, and thus the expectation is that the list `segment_file_paths` has as many elements as the video is seconds long.

# %%
from video_reuse_detector.ffmpeg import get_video_duration
import math

video_duration = get_video_duration(input_file)
assert(math.ceil(video_duration) == len(segment_file_paths))

# %% [markdown]
# ## 2. Downsampling segments

# %% [markdown]
# The extracted video segments are downsampled by extracting individual frames from it, for the purpose of later being aggregated, here only the first video segment is downsampled for the sake of brevity,

# %%
from video_reuse_detector.downsample import downsample

fps = 5
paths_to_extracted_frames = downsample(segment_file_paths[0], fps=5)
assert(len(paths_to_extracted_frames) == fps)

# %% [markdown]
# For every given second in the input to `downsample` an `fps` number of frames are extracted. The extracted frames are uniformly distributed across each second of video.
#
# The resulting extracted frames are shown below,

# %%
# %matplotlib inline

from matplotlib import pyplot as plt
from matplotlib.image import imread

no_of_frames = len(paths_to_extracted_frames)
fig, axs = plt.subplots(1, no_of_frames)

for i in range(no_of_frames):
    axs[i].imshow(imread(paths_to_extracted_frames[i]))
    axs[i].axis('off')

plt.show()

# %% [markdown]
# ## 3. Producing keyframes
#
# The extracted frames in the previous step are aggregated together by
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

keyframe = Keyframe.from_frame_paths(paths_to_extracted_frames)

plt.imshow(rgb(keyframe.image))
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
plt.imshow(rgb(keyframe.image[0:block_height, 0:block_width, :]))
plt.show()

# %% [markdown]
# As a sanity check, we observe that the top, leftmost pixel is expressed by the RGB-tuple,

# %%
top_left_pixel = keyframe.image[0, 0, :]
top_left_pixel

# %% [markdown]
# And the bottom, leftmost pixel is expressed by the RGB-tuple,

# %%
bottom_left_pixel = keyframe.image[block_height, 0, :]
bottom_left_pixel

# %% [markdown]
# And then it stands to reason that the average color for that block is somewhere inbetween those two values,

# %%
from video_reuse_detector.color_correlation import avg_intensity_per_color_channel

average_color_top_left_block = avg_intensity_per_color_channel(keyframe.image[0:block_height, 0:block_width, :])
average_color_top_left_block

# %% [markdown]
# And so the assertions hold,

# %%
assert(top_left_pixel[0] > average_color_top_left_block[0] > bottom_left_pixel[0])
assert(top_left_pixel[1] > average_color_top_left_block[1] > bottom_left_pixel[1])
assert(top_left_pixel[2] > average_color_top_left_block[2] > bottom_left_pixel[2])

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
