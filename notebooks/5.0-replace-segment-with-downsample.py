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
# # Downsampling immediately --- feature parity?
#
# In this notebook we check if skipping the segmentation step has feature parity with segmenting first, and downsampling later.
#
# We begin first by loading a video that we can perform our operations on,

# %%
import os
from pathlib import Path
from IPython.display import Video

import video_reuse_detector.ffmpeg as ffmpeg

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])

video_path = VIDEO_DIRECTORY / 'panorama_augusti_1944.mp4'
assert(video_path.exists())

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
video_path = ffmpeg.slice(video_path, "00:01:30", "00:01:00", OUTPUT_DIRECTORY)
assert(video_path.exists())

# Video expects a relative path in relation to the notebook
Video(str(video_path.relative_to(Path.cwd())))

# %% [markdown]
# Regardless of segmenting the video or not, we want that the frames we extract to be evenly distributed from each second of video. To see that we accomplish this, we extract all the frames from the video,

# %%
import cv2

vidcap = cv2.VideoCapture(str(video_path))
success, image = vidcap.read()

frame_index = 0

frames = []
while success:
    frame_path = OUTPUT_DIRECTORY / f"frame{frame_index}.jpg"
    cv2.imwrite(str(frame_path), image)
    frames.append(frame_path)
    
    success, image = vidcap.read()

    frame_index += 1

print(f'Extracted {len(frames)} number of frames from {video_path}')

# %% [markdown]
# We then show all the frames from the first second of video,

# %%
# %matplotlib inline

from matplotlib import pyplot as plt
from matplotlib.image import imread

def get_frame_rate(file_path: Path) -> float:
    import subprocess
    from fractions import Fraction
    
    ffprobe_cmd = (
        'ffprobe -v 0'
        ' -of csv=p=0'
        ' -select_streams v:0'
        ' -show_entries stream=r_frame_rate'
        f' {str(file_path)}'
    )

    binary_string_w_newline = subprocess.check_output(ffprobe_cmd.split())
    binary_string = binary_string_w_newline.strip()
    as_string = binary_string.decode('ascii')
    as_number = float(Fraction(as_string))
    print(f'Getting framerate for file_path={file_path} yielded {as_string} ({as_number})')
    return as_number

frame_rate = get_frame_rate(video_path)

no_of_frames_per_row = 5

nrows = int(frame_rate / no_of_frames_per_row)
ncols = no_of_frames_per_row  
figsize = [18, 18]              # figure size, inches

# create figure (fig), and array of axes (ax)
fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)

# plot simple raster image on each sub-plot
for frame_id, axi in enumerate(ax.flat):
    # i runs from 0 to (nrows*ncols-1)
    # axi is equivalent with ax[rowid][colid]
    img = frames[frame_id]
    axi.imshow(imread(img))
        
    # get indices of row/column
    row_id = frame_id // ncols
    col_id = frame_id % ncols
    
    # write row/col indices as axes' title for identification
    axi.set_title(f"Frame: {frame_id}. Row: {row_id}, Col: {col_id}")
    axi.axis('off')

plt.show()

# %% [markdown]
# And consequently, 5 frames evenly distributed from that second of video would be,

# %%
fig, axs = plt.subplots(nrows=1, ncols=no_of_frames_per_row, figsize=figsize)
every_fifth_frame = frames[0::5]
for i in range(no_of_frames_per_row):
    axs[i].imshow(imread(every_fifth_frame[i]))
    axs[i].axis('off')

plt.show()

# %% [markdown]
# And then we segment it,

# %%
from video_reuse_detector.segment import segment

# The segments produced by the function need to be written to disk
segment_file_paths = segment(video_path, OUTPUT_DIRECTORY / video_path.stem)

# %% [markdown]
# And downsample the first segment,

# %%
from video_reuse_detector.downsample import downsample

fps = 5
paths_to_extracted_frames_w_segmentation = downsample(segment_file_paths[0], fps=5)[0:5]

# %% [markdown]
# And inspect the frames,

# %%
# %matplotlib inline

from matplotlib import pyplot as plt
from matplotlib.image import imread

no_of_frames_w_segmentation = len(paths_to_extracted_frames_w_segmentation)
fig, axs = plt.subplots(1, no_of_frames_w_segmentation, figsize=figsize)

for i in range(no_of_frames_w_segmentation):
    axs[i].imshow(imread(paths_to_extracted_frames_w_segmentation[i]))
    axs[i].set_title(f"Frame: {i}")
    axs[i].axis('off')

plt.show()

# %% [markdown]
# And compare that against downsampling immediately, without segmenting first,

# %%
from typing import List

# https://stackoverflow.com/a/312464/5045375
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def __downsample__(file_path: Path, output_directory: Path) -> List[List[Path]]:
    ffmpeg_cmd = (
        'ffmpeg'
        f' -i {file_path}'
        f' -r 5'
        f' {output_directory}/frame%07d.png'
    )

    all_frames = ffmpeg.execute(ffmpeg_cmd, output_directory)
    batches = chunks(all_frames, 5)
    
    return batches


# %% [markdown]
# And again, inspect the frames,

# %%
paths_to_extracted_frames_downsample_immediately = list(downsample(video_path, OUTPUT_DIRECTORY / video_path.stem))
no_of_frames = 5
fig, axs = plt.subplots(1, no_of_frames, figsize=figsize)

for i in range(no_of_frames):
    axs[i].imshow(imread(paths_to_extracted_frames_downsample_immediately[i]))
    axs[i].axis('off')

plt.show()

# %% [markdown]
# They are exactly the same.

# %% [markdown]
# To compare the entire flow,

# %%
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from loguru import logger

import video_reuse_detector.util as util
from video_reuse_detector.color_correlation import ColorCorrelation
from video_reuse_detector.downsample import downsample
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.orb import ORB
from video_reuse_detector.segment import segment
from video_reuse_detector.thumbnail import Thumbnail
from video_reuse_detector.fingerprint import FingerprintCollection
from video_reuse_detector.profiling import timeit


from video_reuse_detector import ffmpeg

@timeit
def extract_fingerprint_collection_with_keyframes_w_segmentation(
    file_path: Path, root_output_directory: Path, segment_length_in_seconds=1
) -> Dict[int, Tuple[Keyframe, FingerprintCollection]]:
    assert file_path.exists()

    # Note the use of .stem as opposed to .name, we do not want
    # the extension here,
    segments = segment(
        file_path,
        root_output_directory / file_path.stem,
        segment_length_in_seconds=segment_length_in_seconds,
    )
    
    downsamples = list(map(downsample, segments))
    
    fps = {}

    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions sometimes for videos with a fractional length
            # as the last segment might not contain any frames.
            continue

        segment_id = util.segment_id_from_path(frame_paths[0])

        keyframe = Keyframe.from_frame_paths(frame_paths)
        fpc = FingerprintCollection.from_keyframe(keyframe, file_path.name, segment_id)
        fps[segment_id] = (keyframe, fpc)

    return fps


# %% [markdown]
# Which we will compare against downsampling immediately,

# %%
# https://stackoverflow.com/a/312464/5045375
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@timeit
def extract_fingerprint_collection_with_keyframes(
    file_path: Path, root_output_directory: Path
) -> Dict[int, Tuple[Keyframe, FingerprintCollection]]:
    assert file_path.exists()

    downsamples = chunks(downsample(file_path, root_output_directory / file_path.stem), 5)

    fps = {}

    segment_id = 0
    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions sometimes for videos with a fractional length
            # as the last segment might not contain any frames.
            continue

        keyframe = Keyframe.from_frame_paths(frame_paths)
        fpc = FingerprintCollection.from_keyframe(keyframe, file_path.name, segment_id)
        fps[segment_id] = (keyframe, fpc)

        segment_id += 1


    return fps

# %% [markdown]
# To ascertain which method is faster,

# %%
_, segment_first_processing_time = extract_fingerprint_collection_with_keyframes_w_segmentation(video_path, OUTPUT_DIRECTORY)
_, downsample_immediately_processing_time = extract_fingerprint_collection_with_keyframes(video_path, OUTPUT_DIRECTORY)
print(segment_first_processing_time)
print(downsample_immediately_processing_time)

# %% [markdown]
# Seemingly, skipping segmentation is quicker. We check for a few more files,

# %%
videos = [f for f in VIDEO_DIRECTORY.iterdir() if f.suffix != '.md']
assert len(videos) > 0

no_of_videos = 5
videos = videos[0:5]

# Note: can contain None values
all_video_durations = {video.name: ffmpeg.get_video_duration(video) for video in videos}

video_durations = {k: v for k,v in all_video_durations.items() if v is not None}

def benchmark_fingerprint_extraction(videos, extract):
    benchmarks = {}

    videos_benchmarked = 1
    for video_path in videos:
        print(f'Extracting fingerprints from {video_path} ({videos_benchmarked}/{len(videos)})')
        _, execution_time = extract(video_path, OUTPUT_DIRECTORY)
        benchmarks[video_path.name] = execution_time
        videos_benchmarked += 1

    return benchmarks

def save_to_csv(benchmarks, csv_label):
    import datetime

    BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    benchmarks_csv = (
        "extraction_benchmarks"
        f"_{csv_label}"
        f"_{timestamp}"
        ".csv"
    )

    benchmarks_csv = BENCHMARKS_DIRECTORY / benchmarks_csv
    benchmarks_csv.parent.mkdir(parents=True, exist_ok=True)

    print(f"Outputting results to {benchmarks_csv}")

    with open(str(benchmarks_csv), 'w') as f:
        header = "Name,Video Duration,Processing Time"
        print(f"Writing header={header}")
        f.write(f'{header}\n')
    
        # We use the sorted dictionary here, it makes plotting easier later on
        for video_name, processing_time in benchmarks.items():
            content = f'{video_name},{video_durations[video_name]},{processing_time}'
            print(f"Writing content={content} to {benchmarks_csv}")
            f.write(f"{content}\n")

    return benchmarks_csv


# %% [markdown]
# To benchmark the method that uses segmentation we have

# %%
benchmarks_w_segmentation = benchmark_fingerprint_extraction(videos, extract_fingerprint_collection_with_keyframes_w_segmentation)
benchmarks_csv_w_segmentation = save_to_csv(benchmarks_w_segmentation, "with_segmentation")

# %% [markdown]
# And without segmentation

# %%
benchmarks_skip_segmentation = benchmark_fingerprint_extraction(videos, extract_fingerprint_collection_with_keyframes)
benchmarks_csv_skip_segmentation = save_to_csv(benchmarks_skip_segmentation, "skip_segmentation")

# %% [markdown]
# And to compare,

# %%
import pandas as pd

w_segmentation_df = pd.read_csv(str(benchmarks_csv_w_segmentation))
w_segmentation_df = w_segmentation_df.sort_values(by=['Video Duration'], ascending=[False])
print(w_segmentation_df.head())

skip_segmentation_df = pd.read_csv(str(benchmarks_csv_skip_segmentation))
skip_segmentation_df = skip_segmentation_df.sort_values(by=['Video Duration'], ascending=[False])
print(skip_segmentation_df.head())

w_segmentation_df.set_index('Video Duration')['Processing Time'].plot()
skip_segmentation_df.set_index('Video Duration')['Processing Time'].plot()

plt.legend([benchmarks_csv_w_segmentation.name, benchmarks_csv_skip_segmentation.name])
plt.ylabel('Processing Time')
plt.xlabel('Video Duration')
plt.axes().xaxis.grid(True)
plt.show()

# %% [markdown]
# Overall, skipping segmentation seems like a winner!
