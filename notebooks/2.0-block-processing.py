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


# %% [markdown]
# And now, for a generic image,

# %%
def compute_block_size(image, nr_of_blocks=16):
    height, width, _ = image.shape
    block_height = int(round(height / nr_of_blocks))
    block_width = int(round(width / nr_of_blocks))

    return (block_height, block_width)


def mean_per_color_channel(block):
    avg_color_per_row = np.average(block, axis=0)
    avg_intensity_per_channel = np.average(avg_color_per_row, axis=0)

    assert(len(avg_intensity_per_channel) == 3)  # Three channels

    return avg_intensity_per_channel


def color_transformation_and_block_splitting(image, nr_of_blocks=16):
    im_h, im_w = image.shape[:2]
    bl_h, bl_w = compute_block_size(image, nr_of_blocks)

    # A new image that is a downsampling of the original where the average
    # intensities of each block are stored, i.e. consider the top-most left
    # block of our original image, then the first element in this matrix will
    # be the average intensity (per channel) of that block,
    average_intensities = np.zeros((bl_h, bl_w, 3))

    row_offset = int(round(bl_h/nr_of_blocks))
    col_offset = int(round(bl_w/nr_of_blocks))

    # Process the original image in blocks of our established sizes,
    for row in np.arange(im_h - bl_h + 1, step=bl_h):
        for col in np.arange(im_w - bl_w + 1, step=bl_w):
            avgs = mean_per_color_channel(image[row:row+bl_h, col:col+bl_w])

            # The index of the block which we just processed,
            block_row_idx = int(round(row/bl_h))
            assert(block_row_idx < nr_of_blocks)
            block_col_idx = int(round(col/bl_w))
            assert(block_col_idx < nr_of_blocks)

            # The index in the new, downsampled, image called
            # "average_intensities", where our result "avgs" will go,
            r = block_row_idx * row_offset
            c = block_col_idx * col_offset

            average_intensities[r:r+row_offset, c:c+col_offset] = avgs

    return average_intensities

import scipy.misc

f = scipy.misc.face()

averages = color_transformation_and_block_splitting(f)
plt.subplot(121); plt.imshow(f)
plt.subplot(122); plt.imshow(averages.astype(np.uint8))

plt.show()
