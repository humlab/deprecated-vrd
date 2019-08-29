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
# # ORB Exploration
#
# This notebook is meant to explore rudimentarily how to use ORB in OpenCV

# %%
import cv2
import skimage

# %matplotlib notebook
from matplotlib import pyplot as plt

astronaut = skimage.data.astronaut()

# Convert the astronaut image so it can be used with OpenCV
astronaut = skimage.img_as_ubyte(astronaut)

# Note we use ORB_create instead of ORB as the latter invocation
# results in a TypeError, specifically,
#
# TypeError: Incorrect type of self (must be 'Feature2D' or its derivative)
#
# because of a compatability issue (wrapper related), see
# https://stackoverflow.com/a/49971485
orb = cv2.ORB_create()

# find the keypoints with ORB
kps = orb.detect(astronaut, None)

img = cv2.drawKeypoints(astronaut, kps, None, color=(0, 255, 0), flags=0)

plt.imshow(img)
plt.show()
