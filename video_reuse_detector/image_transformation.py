import numpy as np
import cv2

from typing import List

from video_reuse_detector import util


def average(images: List[np.ndarray]) -> np.ndarray:
    """Average all the elements in the input matrices producing a new matrix
    such that the output is a new image, and thus the new "average" is not
    a mathematical average, but rounded to the nearest integer values.

    All input arrays are assumed to be of the same size.
    """
    avg = np.zeros(images[0].shape, np.float)

    for image in images:
        avg += image/len(images)

    return np.array(np.round(avg), dtype=np.uint8)


def interpolation_method(scale_factor):
    # Another option for upscaling is INTER_CUBIC which is slower but
    # produces a better looking output. Using INTER_LINEAR for now
    return cv2.INTER_LINEAR if scale_factor >= 1 else cv2.INTER_AREA


def scale(image, scale_factor):
    height, width, _ = image.shape
    new_height, new_width = int(height*scale_factor), int(width*scale_factor)
    interpolation = interpolation_method(scale_factor)

    return cv2.resize(image, (new_height, new_width), interpolation)


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def fold(image: np.ndarray) -> np.ndarray:
    """
    Takes a given image and folds it so that the resulting output image is
    invariant against horizontal attacks,

    While the input is semantically an image, it will accept any numpy array.
    We will use the words image, array, and matrix, interchangably when
    referring to the input and output here.

    So, for

    >>> import numpy as np
    >>> image = np.arange(6).reshape(3, 2)
    >>> folded_image = fold(image)

    the output will satisfy the following conditions,

    Condition 1. The shape of the input "image" is retained,

    >>> folded_image.shape == image.shape
    True

    Condition 2. The output matrix, when flipped horizontally, will remain
    unchanged,

    >>> flip_horizontal = lambda image: cv2.flip(image, 1)
    >>> np.array_equal(folded_image, flip_horizontal(folded_image))
    True
    """
    return cv2.addWeighted(image, 0.5, cv2.flip(image, 1), 0.5, 0)


def __map_over_blocks__(image, f, no_of_blocks):
    block_img = np.zeros(image.shape)
    im_h, im_w = image.shape[:2]
    bl_h, bl_w = util.compute_block_size(image, no_of_blocks)

    for row in np.arange(im_h - bl_h + 1, step=bl_h):
        for col in np.arange(im_w - bl_w + 1, step=bl_w):
            block_to_process = image[row:row+bl_h, col:col+bl_w]
            block_img[row:row+bl_h, col:col+bl_w] = f(block_to_process)

    return block_img


def normalized_grayscale(image: np.ndarray, no_of_blocks) -> np.ndarray:
    def zscore(block):
        mean = np.mean(block)
        std = np.std(block)
        return mean - std

    return __map_over_blocks__(grayscale(image), zscore, no_of_blocks)
