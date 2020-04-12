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
from notebook_util import VideoSelector
    
video_selection = VideoSelector()

# %%
video_selection

# %%
print(f'Selected {video_selection.value}')

# %%
from IPython.display import Video
from pathlib import Path

if (len(video_selection.value) > 0):
    Video(Path(video_selection.value[0]))

# %%
