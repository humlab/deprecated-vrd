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
# # Compare FingerprintComputationComparison Processing Data
#
# In this notebook we compare performance data between CSV-files for processing time with regards to computing fingerprints after changing the flags to ffmpeg for segmentation,

# %%
import os
from pathlib import Path
import datetime

BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

prev_computation = BENCHMARKS_DIRECTORY / 'Fingerprint_Collection_Computation_2020-02-24_18-52-43.csv'
new_computation = BENCHMARKS_DIRECTORY / 'Fingerprint_Collection_Computation_2020-02-24_21-09-09.csv'

assert prev_computation != new_computation

# %% [markdown]
# And then we plot the data. First, as a bar chart for each respective video,

# %%
import pandas as pd
import matplotlib.pyplot as plt

before_copy_codec = pd.read_csv(str(prev_computation))
before_copy_codec = before_copy_codec.sort_values(by=['Video Duration'], ascending=[False])
print(before_copy_codec.head())

after_copy_codec = pd.read_csv(str(new_computation))
after_copy_codec = after_copy_codec.sort_values(by=['Video Duration'], ascending=[False])
print(after_copy_codec.head())

before_copy_codec.set_index('Video Duration')['Processing Time'].plot()
after_copy_codec.set_index('Video Duration')['Processing Time'].plot()

plt.legend([prev_computation.name, new_computation.name])
plt.ylabel('Processing Time')
plt.xlabel('Video Duration')
plt.axes().xaxis.grid(True)
plt.show()

# %% [markdown]
# Overall we saw a marked improvement from the following change,
#
# ```
#     ffpeg_cmd = (
#          'ffmpeg'
#          f' -i {input_video}'
# -        ' -codec:v libx264'
#          f' -force_key_frames expr:gte(t,n_forced*{segment_length_in_seconds})'
#          ' -map 0'
#          ' -f segment'
#          f' -segment_time {segment_length_in_seconds}'
# -        f' {output_directory}/{input_video.stem}-segment%03d.mp4'
# +        ' -vcodec copy'
# +        f' {output_directory}/{input_video.stem}-segment%03d{input_video.suffix}'
#      )
# ```
#
# but the print-outs of the dataframes implies that the ability to process `.asf`-files have been lost.
