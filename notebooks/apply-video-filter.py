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
from notebook_util import video_selector

video_selection = video_selector(select_multiple=True)

# %%
video_selection

# %%
print(f'Selected {video_selection.value}')

# %%
import ipywidgets as widgets
import video_reuse_detector.ffmpeg as ffmpeg

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
from pathlib import Path
import os

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
OUTPUT_DIRECTORY.mkdir(exist_ok=True)
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
from IPython.display import Video

Video(outputs[0].relative_to(Path.cwd()))

# %%
