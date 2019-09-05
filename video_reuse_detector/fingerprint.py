import numpy as np
import cv2

from typing import List, Dict
from dataclasses import dataclass

from pathlib import Path

import image_transformation


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


def equalize_histogram(image):
    return cv2.equalizeHist(image_transformation.grayscale(image))


def produce_normalized_grayscale_image(image, strategy=equalize_histogram):
    """
    TODO: Page 64 of the paper describes a difference approach for normalizing
    the grayscale image that is something akin to,

    grayscale_image = grayscale(image).astype(numpy.float32) / 255

    grayscale_image -= grayscale_image.mean()
    grayscale_image /= grayscale_image.std()
    normalized_image = grayscale_image

    And finally,
    return normalized_image * 255

    but applied on a block-by-block basis. Let this serve as a place-holder
    for now and re-visit this portion of the code later.
    """
    return strategy(image)


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
class ColorCorrelation:
    histogram: Dict[str, float]
    as_number: int
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'ColorCorrelation':
        import color_correlation

        cc_hist = color_correlation.color_correlation_histogram(keyframe.image)
        encoded = color_correlation.feature_representation(cc_hist)
        return ColorCorrelation(cc_hist, encoded, keyframe, keyframe.metadata)
