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


# %% [markdown]
# And then, if we combine several of these

# %%
def checkerboard(rows, columns, channels, color):
    board = np.ones((rows, columns, channels))

    board[::2, 1::2, :] = color
    board[1::2, ::2, :] = color

    return board


def simple_checkerboard(color):
    return checkerboard(2, 2, 3, color)


import numpy as np
black_board = simple_checkerboard(black)
red_board   = simple_checkerboard(color=(1, 0, 0))  # (R, G, B)
green_board = simple_checkerboard(color=(0, 1, 0))
blue_board  = simple_checkerboard(color=(0, 0, 1))

top_half    = np.hstack((black_board, red_board))
bottom_half = np.hstack((green_board, blue_board))

board = np.vstack((top_half, bottom_half))

plt.imshow(board)

# %%
