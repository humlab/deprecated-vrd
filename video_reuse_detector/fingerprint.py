import numpy as np
import cv2

from typing import List, Dict
from dataclasses import dataclass

from pathlib import Path

from video_reuse_detector import util, image_transformation


def crop_with_central_alignment(image, m=320, n=320):
    """
    Crops the given image to a (M x N) area with central alignment
    """
    height, width, _ = image.shape
    center_y, center_x = height/2, width/2
    starting_row, starting_column = int(center_y - m/2), int(center_x - n/2)

    img = image[starting_row:starting_row + m,
                starting_column:starting_column + n]

    return img


def average_frames(frames):
    """
    Average the given set of frames equally across all pixel values and
    channels as per Eq. 4.1.
    """
    return image_transformation.average(frames)


def fold(image):
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


def map_over_blocks(image, f, nr_of_blocks=16):
    block_img = np.zeros(image.shape)
    im_h, im_w = image.shape[:2]
    bl_h, bl_w = util.compute_block_size(image, nr_of_blocks)

    for row in np.arange(im_h - bl_h + 1, step=bl_h):
        for col in np.arange(im_w - bl_w + 1, step=bl_w):
            block_to_process = image[row:row+bl_h, col:col+bl_w]
            block_img[row:row+bl_h, col:col+bl_w] = f(block_to_process)

    return block_img


def produce_normalized_grayscale_image(image):
    def zscore(block):
        mean = np.mean(block)
        std = np.std(block)
        return mean - std

    return map_over_blocks(image_transformation.grayscale(image), zscore)


def produce_thumbnail(image, m=30):
    folded_grayscale = fold(produce_normalized_grayscale_image(image))

    # Assume that converting the image to a m x m image is effectively
    # downsizing the image, hence interpolation=cv2.INTER_AREA
    return cv2.resize(folded_grayscale, (m, m), interpolation=cv2.INTER_AREA)


@dataclass
class FingerprintMetadata:
    video_source: Path
    segment_id: int


@dataclass
class Keyframe:
    image: np.ndarray
    metadata: FingerprintMetadata

    @staticmethod
    def from_frames(video_source: Path,
                    segment_id: int,
                    frames: List[np.ndarray]) -> 'Keyframe':
        kf = average_frames(frames)
        kf = image_transformation.scale(kf, scale_factor=1.2)
        kf = crop_with_central_alignment(kf)

        metadata = FingerprintMetadata(video_source, segment_id)

        return Keyframe(kf, metadata)


@dataclass
class Thumbnail:
    image: np.ndarray
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'Thumbnail':
        thumb = produce_thumbnail(keyframe.image)
        return Thumbnail(thumb, keyframe, keyframe.metadata)


@dataclass
class ORB:
    descriptors: List[List[int]]
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'ORB':
        # TODO: Use folded variant, but OpenCV freaks out
        f_grayscale = image_transformation.grayscale(keyframe.image)

        # Note we use ORB_create() instead of ORB() as the latter invocation
        # results in a TypeError, specifically,
        #
        # TypeError: Incorrect type of self (must be 'Feature2D' or its
        # derivative)
        #
        # because of a compatability issue (wrapper related), see
        # https://stackoverflow.com/a/49971485
        #
        # We set nfeatures=250 as per p. 103 in the paper.
        orb = cv2.ORB_create(nfeatures=250, scoreType=cv2.ORB_FAST_SCORE)

        # find the keypoints with ORB
        kps, des = orb.detectAndCompute(f_grayscale, None)

        if des is None:
            des = []  # No features found

        return ORB(des, keyframe, keyframe.metadata)


@dataclass
class ColorCorrelation:
    histogram: Dict[str, float]
    as_number: int
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'ColorCorrelation':
        from video_reuse_detector import color_correlation

        cc_hist = color_correlation.color_correlation_histogram(keyframe.image)
        encoded = color_correlation.feature_representation(cc_hist)
        return ColorCorrelation(cc_hist, encoded, keyframe, keyframe.metadata)
