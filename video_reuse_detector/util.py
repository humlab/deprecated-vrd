from pathlib import Path
from typing import Union

import cv2
import numpy as np


def compute_block_size(image, nr_of_blocks=16):
    height, width = image.shape[:2]
    block_height = int(round(height / nr_of_blocks))
    block_width = int(round(width / nr_of_blocks))

    return (block_height, block_width)


def segment_id_from_path(path_or_str: Union[Path, str]) -> int:
    """Extracts segment_id from a given path

    >>> segment_id_from_path('/path/to/videoname/segment/000/frame001.png')
    0

    >>> path = Path('/path/to/videoname/segment/000/frame001.png')
    >>> segment_id_from_path(path)
    0
    """
    # For a path on the form,
    #
    # /some/path/to/videoname/segment/000/frame001.png
    #
    # then path.parents[0] is
    #
    # /some/path/to/videoname/segment/000
    #
    # and path.parents[0].stem is "000"
    path = Path(path_or_str)  # Path(Path(...)) is idempotent
    return int(str(path.parents[0].stem))


def video_name_from_path(path_or_str: Union[Path, str]) -> str:
    """Extracts the video name from a given path

    >>> video_name_from_path('/path/to/videoname/segment/000/frame001.png')
    'videoname'

    >>> path = Path('/path/to/videoname/segment/000/frame001.png')
    >>> video_name_from_path(path)
    'videoname'
    """
    # For a path on the form,
    #
    # /some/path/to/videoname/segment/000/frame001.png
    #
    # then path.parents[2] is
    #
    # /some/path/to/videoname/
    #
    # and path.parents[2].stem is "videoname"
    path = Path(path_or_str)
    return str(path.parents[2].stem)


def imread(path_or_str: Union[Path, str]) -> np.ndarray:
    cv2_compatible_path = str(path_or_str)
    return cv2.imread(cv2_compatible_path)


def imwrite(path_or_str: Union[Path, str], image: np.ndarray):
    cv2_compatible_path = str(path_or_str)
    cv2.imwrite(cv2_compatible_path, image)
