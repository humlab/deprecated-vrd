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
# We can now plot the video durations,

# %%
import pandas as pd
import matplotlib.pyplot as plt

df_durations = pd.DataFrame.from_dict(video_durations, orient='index')
df_durations = df_durations.sort_values(by=0, ascending=[True])

# Plot in descending order of runtime
df_durations.plot(kind='barh', grid=False, figsize=(len(videos), 18))
plt.xlabel('Video Duration in Seconds')
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
def benchmark_segmentation(videos, segment_length):
    benchmarks = {}

    videos_benchmarked = 1
    for video_path in videos:
        print(f'Segmenting {video_path} ({videos_benchmarked}/{len(videos)})')
        _, execution_time = __segment__(video_path, OUTPUT_DIRECTORY)
        benchmarks[video_path.name] = execution_time
        videos_benchmarked += 1

    return benchmarks


# %% [markdown]
# And to we write the results to a CSV-file to enable historical comparisons,

# %%
def save_to_csv(benchmarks, segment_length):
    import datetime

    BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    benchmarks_csv = (
        "segment_benchmarks"
        f"_w_length={segment_length}"
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
# Executing it,

# %%
segment_length = 1
benchmarks = benchmark_segmentation(videos, segment_length)
benchmarks_csv = save_to_csv(benchmarks, segment_length)

# %% [markdown]
# And then we can plot how processing time is dependent on video duration

# %%
df_every_second = pd.read_csv(str(benchmarks_csv))
df_every_second = df_every_second.sort_values(by=['Video Duration'], ascending=[True])

df_every_second.set_index('Name', inplace=True, drop=True)
ax = df_every_second.plot.barh(figsize=(len(videos), 18))

plt.show()

# %%
ax = df_every_second.plot.line()
ax.set_xticks(range(len(df_every_second)));
ax.set_xticklabels(df_every_second.index, rotation=90);
plt.show()

# %%
df_every_second.set_index('Video Duration')['Processing Time'].plot()
plt.show()

# %% [markdown]
# Evidently, the time it takes to segment a video is very much a function of its length.
