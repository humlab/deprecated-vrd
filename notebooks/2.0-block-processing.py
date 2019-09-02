# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.2'
#       jupytext_version: 1.2.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# 2.0 Block Processing
# ===
#
# In this notebook, we simply explore how to process "images" on a block-by-block basis
#
# First, we create a very simple checkerboard,

# %%
import numpy as np

simple_checkerboard = np.ones((2, 2, 3))

# RGB-values expressed as (R, G, B) with values ranging from zero to one
black = (0, 0, 0)
simple_checkerboard[::2, 1::2, :] = black
simple_checkerboard[1::2, ::2, :] = black

# %matplotlib inline
import matplotlib.pyplot as plt

plt.imshow(simple_checkerboard)
