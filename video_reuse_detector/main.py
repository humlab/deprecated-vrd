import cv2
import image_transformation
import video

from pathlib import Path

"""
This code implements the fingerprinting method proposed by Zobeida Jezabel
Guzman-Zavaleta in the thesis "An Effective and Efficient Fingerprinting Method
for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis,
specifically from the section 5.4 Discussion, where the author details the
parameter values that "proved" the "best" during her experiments.
"""


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


def keyframe(frames):
    kf = average_frames(frames)
    kf = image_transformation.scale(kf, scale_factor=1.2)
    return crop_with_central_alignment(kf)


def imread(filename: Path):
    return cv2.imread(str(filename))


def imwrite(filename: Path, image):
    filename.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(filename), image)


def produce_fingerprints(input_video: Path, output_directory: Path):
    # TODO: Produce audio fingerprints, this just creates keyframes
    # TODO: Clean-up intermediary directories
    segments_dir = output_directory / 'segments'
    frames_dir = output_directory / 'frames'
    segments = video.segment(input_video, segments_dir)

    segment_id = 0
    for segment in segments:
        frames_output_directory = frames_dir / f'segment{segment_id:03}'
        frame_paths = video.downsample(segment, frames_output_directory)

        kf_dir = output_directory / 'keyframes'
        kf = keyframe([imread(filename) for filename in frame_paths])

        imwrite(kf_dir / f'{input_video.stem}-keyframe{segment_id:03}.png', kf)

        thumbs_dir = output_directory / 'thumbs'
        thumb = produce_thumbnail(kf)
        imwrite(thumbs_dir / f'{input_video.stem}-thumb{segment_id:03}.png', thumb)  # noqa: E501
        segment_id += 1


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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
