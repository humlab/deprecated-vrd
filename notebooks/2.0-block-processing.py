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
plt.show()


# %% [markdown]
# And then, if we combine several of these boards into a new checkerboard

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
plt.show()

# %% [markdown]
# we can then operate on blocks that are the same size as each "sub"-board. Here, we first view the board as a matrix of blocks,

# %%
import skimage.util

assert(black_board.shape == red_board.shape == green_board.shape == blue_board.shape)
block_shape = black_board.shape

# view the board as a matrix of blocks (of shape block_shape)
view = skimage.util.view_as_blocks(board, block_shape)

assert(np.array_equal(black_board, view[0][0][0]))
assert(np.array_equal(red_board,   view[0][1][0]))
assert(np.array_equal(green_board, view[1][0][0]))
assert(np.array_equal(blue_board,  view[1][1][0]))

# collapse the last two dimensions in one
flatten_view = view.reshape(view.shape[0], view.shape[1], -1)

# %% [markdown]
# And then, we compute the mean of each checkerboard,

# %%
# Compute the mean for each sub-checkerboard,
mean_view = np.mean(flatten_view, axis=2)

# Then, the number of means should be equal to the number of boards,
boards = [black_board, red_board, green_board, blue_board]
assert(len(boards) == len(mean_view.flatten()))

# %% [markdown]
# And now, if we plot that,

# %%
plt.imshow(mean_view)
plt.show()

# %% [markdown]
# We observe that the mean of the three colored checkerboards are the same and this is expected as the mean is smeared across all channels here. And if the image we were processing was in grayscale, this would be satisfactory.

# %% [markdown]
# ## Color mean on a channel-by-channel basis
#
# However, if we want to compute the mean on a channel-by-channel basis, it is our processing that must change.
#
# Take for instance the so-called `red_board`, we expect the average to be half-way between red and white, which we visualise by performing the following computations,

# %%
avg_color_per_row = np.average(red_board, axis=0)
avg_intensity_per_channel = np.average(avg_color_per_row, axis=0)

plt.axes()
square = plt.Rectangle((10, 10), 100, 100, fc=avg_intensity_per_channel)
plt.gca().add_patch(square)

plt.axis('scaled')
plt.axis('off')
plt.show()


# %% [markdown]
# And, for reference we illustrate the average for each checkerboard like so,

# %%
def get_color_average(matrix):
    _, _, channels = matrix.shape
    assert(channels == 3)

    avg_color_per_row = np.average(matrix, axis=0)

    return np.average(avg_color_per_row, axis=0)


def square(color, x, y, side_length):
    return plt.Rectangle((x, y), side_length, side_length, fc=color)


plt.axes()

x, y = 10, 10
side_length = 100
padding = 10

for b in boards:
    color = get_color_average(b)
    plt.gca().add_patch(square(color, x, y, side_length))
    x += padding + side_length

plt.axis('scaled')
plt.axis('off')
plt.show()

# %% [markdown]
# And now, to compute this on a block-by-block-basis, where each block is one of the checkerboards, we do as follows,

# %%
block_img = np.zeros(block_shape)
im_h, im_w = board.shape[:2]
bl_h, bl_w = 2, 2

for row in np.arange(im_h - bl_h + 1, step=bl_h):
    for col in np.arange(im_w - bl_w + 1, step=bl_w):
        block_row_idx = int(round(row/bl_h))
        block_col_idx = int(round(col/bl_w))

        block_img[block_row_idx, block_col_idx] = get_color_average(board[row:row+bl_h, col:col+bl_w])

plt.imshow(block_img)
plt.show()
