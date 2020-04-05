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

# %%
import ipywidgets as widgets
import os
from pathlib import Path
from IPython.display import Video

import video_reuse_detector.ffmpeg as ffmpeg

VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])
videos = [str(f) for f in VIDEO_DIRECTORY.iterdir() if f.suffix != '.md' and f.suffix != '.txt']

video_selection = widgets.SelectMultiple(
    options=videos,
    description='Video:',
    disabled=False,
)

# %%
video_selection

# %%
print(f'Selected {video_selection.value}')

# %%
import IPython

available_filters = ffmpeg.filters()
filter_selection = widgets.SelectMultiple(
    options=list(available_filters.keys()),
    description='Filters',
    disabled=False
)

# %%
filter_selection

# %%
print(f'Selected {filter_selection.value}')

# %%
OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
outputs = []

print(video_selection.value)
print(filter_selection.value)

for video in video_selection.value:
    for f in filter_selection.value:
        print(f'Applying {f} to {video}')
        result = available_filters[f](Path(video), OUTPUT_DIRECTORY)
        outputs.append(result)
        print(f'Produced {result}')

# %%
Video(outputs[0].relative_to(Path.cwd()))

# %%
