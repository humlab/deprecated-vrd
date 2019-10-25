import numpy as np

from dataclasses import dataclass
from pathlib import Path
from typing import List

from loguru import logger

from video_reuse_detector import image_transformation
import video_reuse_detector.util as util


def average_frames(frames):
    """
    Average the given set of frames equally across all pixel values and
    channels as per Eq. 4.1.
    """
    return image_transformation.average(frames)


def crop_with_central_alignment(image: np.ndarray, m=320, n=320):
    """
    Crops the given image to a (M x N) area with central alignment
    """
    height, width, _ = image.shape
    center_y, center_x = height/2, width/2
    starting_row, starting_column = int(center_y - m/2), int(center_x - n/2)

    return image[starting_row:starting_row + m,
                 starting_column:starting_column + n]


@dataclass
class Keyframe:
    image: np.ndarray

    @staticmethod
    def from_frames(frames: List[np.ndarray]) -> 'Keyframe':
        kf = average_frames(frames)
        kf = image_transformation.scale(kf, scale_factor=1.2)
        kf = crop_with_central_alignment(kf)

        return Keyframe(kf)


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='Keyframe extractor')

    parser.add_argument(
        'input_frames',
        nargs='+',
        default=sys.stdin,
        help='The frames to average into a keyframe')

    args = parser.parse_args()

    logger.debug(f'Reading {args.input_frames} as images')
    frames = list(map(util.imread, args.input_frames))
    keyframe = Keyframe.from_frames(frames)

    frame_paths = list(map(Path, args.input_frames))

    # Determine write destination by using the path to the
    # first input image (this is "safe" because all paths
    # within the group are assumed to belong to the same segment),
    # which we verify here,
    def has_parent_equal_to(p, parent): return p.parent == parent
    parent = frame_paths[0].parent

    if not all(has_parent_equal_to(p, parent) for p in frame_paths):
        logger.error((f'Expected all paths in {frame_paths}'
                      ' to have same parent directory'))
        exit(-1)

    # so postulate you have a set of frame paths such as,
    #
    # frame_paths[0] path/to/interim/Megamind/segment/010/frame001.png
    # frame_paths[1] path/to/interim/Megamind/segment/010/frame002.png
    # ...
    #
    # then frame_paths[0].parent is equal to,
    #
    # "path/to/interim/Megamind/segment/010/"
    #
    # which is our destination
    destination_path = str(frame_paths[0].parent / 'keyframe.png')
    util.imwrite(destination_path, keyframe.image)

    print(destination_path)
