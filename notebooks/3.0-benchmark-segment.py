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
# # 3.0 Benchmark `segment`
#
# In this notebook we will ascertain how long it takes to segment a video as a function of its runtime.
#
# We will utilise all videos in `os.environ['VIDEO_DIRECTORY']`.

# %%
import os
from pathlib import Path

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])
assert VIDEO_DIRECTORY.exists()

# %% [markdown]
# We take care to exclude any non-video files,

# %%
videos = [f for f in VIDEO_DIRECTORY.iterdir() if f.suffix != '.md']
assert len(videos) > 0

# %% [markdown]
# Before collecting the respective runtime durations of each video,

# %%
import video_reuse_detector.ffmpeg as ffmpeg

# Note: can contain None values
all_video_durations = {video.name: ffmpeg.get_video_duration(video) for video in videos}

video_durations = {k: v for k,v in all_video_durations.items() if v is not None}

# For the following videos there was a problem in fetching the video duration
if len(videos) != len(all_video_durations):
    print('Could not fetch the video duration for the following files')
    print(set(all_video_durations.keys()) - set(video_durations.keys()))
else:
    print('All OK')

# %% [markdown]
# To make our visualizations easier to digest, we sort the durations. 

# %%
from collections import OrderedDict
from operator import itemgetter

sorted_durations = OrderedDict(sorted(video_durations.items(), key=itemgetter(1)))

# %% [markdown]
# `sorted_durations` will be sorted in ascending order, i.e., `list(sorted_durations.keys())[0]` will be the shortest video, but as we transpose the data the plot will render the runtime of the longest video at the top. This is not important, but mentioned to reduce any would be confusion.

# %%
import pandas as pd
import matplotlib.pyplot as plt

# Sort in descending order of runtime
data = pd.DataFrame.from_records([sorted_durations], index=['video duration in seconds'])

# Plot in descending order of runtime
data.T.plot(kind='barh', grid=False, figsize=(len(videos), 18))
plt.xlabel('seconds')
plt.axes().xaxis.grid(True)
plt.show()

# %% [markdown]
# To discern how long it takes to segment a single video, we utilise the profiling utility `timeit`,

# %%
from video_reuse_detector.profiling import timeit
from video_reuse_detector.segment import segment
import video_reuse_detector.ffmpeg as ffmpeg

@timeit
def __segment__(input_video, output_directory):
    return segment(input_video, output_directory / input_video.stem)

# As this is merely to showcase how to benchmark the segment function, we extract a
# short video to cut down on execution time.
OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
example_video = ffmpeg.slice(videos[0], "00:00:00", "00:00:05", OUTPUT_DIRECTORY)

_, execution_time = __segment__(example_video, OUTPUT_DIRECTORY)
execution_time

# %% [markdown]
# Then, to record the time it takes to segment each video we have,

# %%
benchmarks = {}

for video_path in videos:
    _, execution_time = __segment__(video_path, OUTPUT_DIRECTORY)
    benchmarks[video_path.name] = execution_time

# %% [markdown]
# And then we write the results to a CSV-file to enable historical comparisons,

# %%
import datetime

video_names = [v.name for v in videos]

BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

benchmarks_csv = f"segment_benchmarks_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.csv"
benchmarks_csv = BENCHMARKS_DIRECTORY / benchmarks_csv
benchmarks_csv.parent.mkdir(parents=True, exist_ok=True)

with open(str(benchmarks_csv), 'w') as f:
    f.write('Name,Video_Duration,Processing_Time\n')
    
    # We use the sorted dictionary here, it makes plotting easier later on
    for video_name in sorted_durations.keys():
        f.write(f"{video_name},{video_durations[video_name]},{benchmarks[video_name]}\n")

# %% [markdown]
# And then we can plot how processing time is dependent on video duration. First, we place the two next to one another,

# %%
df = pd.read_csv(str(benchmarks_csv))
df.head()

df.set_index('Name', inplace=True, drop=True)
ax = df.plot.barh(figsize=(len(videos), 18))

df.head()
plt.show()

# %%
ax = df.plot.line()
ax.set_xticks(range(len(df)));
ax.set_xticklabels(df.index, rotation=90);
plt.show()

# %%
df.set_index('Video_Duration').Processing_Time.plot()
plt.show()

# %% [markdown]
# Evidently, the time it takes to segment a video is very much a function of its length.
