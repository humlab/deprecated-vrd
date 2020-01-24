from dataclasses import dataclass
from typing import List, TypeVar

import cv2
import numpy as np

from video_reuse_detector import image_transformation


T = TypeVar('T')


def flatten(nested_list: List[List[T]]) -> List[T]:
    import itertools

    return list(itertools.chain(*nested_list))


# Look-up table for similarity comparison.
# See https://stackoverflow.com/a/58098034/5045375
lu = sum(np.unravel_index(np.arange(256), 8 * (2, )))


def detect_and_extract(image: np.ndarray):
    if len(image.shape) > 3:
        raise ValueError('Expected input image to be a grayscale image')

    # Note we use ORB_create() instead of ORB() as the latter invocation
    # results in a TypeError, specifically,
    #
    # TypeError: Incorrect type of self (must be 'Feature2D' or its
    # derivative)
    #
    # because of a compatability issue (wrapper related), see
    # https://stackoverflow.com/a/49971485
    orb = cv2.ORB_create(scoreType=cv2.ORB_FAST_SCORE)

    # TODO: replace with skimage.feature.orb.detect_and_extract?
    return orb.detectAndCompute(image, None)


@dataclass
class ORB:
    keypoints: List[List[int]]
    descriptors: List[List[int]]

    @staticmethod
    def from_image(image: np.ndarray) -> 'ORB':
        folded = image_transformation.fold(image)
        # TODO: Use the same normalizing grayscale as used for thumbnails?
        # i.e.,
        # grayscale = image_transformation.normalized_grayscale
        # grayscale(folded, 16).astype(np.uint8)
        f_grayscale = image_transformation.grayscale(folded)

        kps, des = detect_and_extract(f_grayscale)

        if des is None:
            des = []  # No features found

        return ORB(kps, des)

    @staticmethod
    def compute_percentage(no_of_good_matches, no_of_possible_matches):
        percentage = no_of_good_matches/no_of_possible_matches

        if percentage >= 0.7:
            return (no_of_good_matches, 1.0)
        if percentage >= 0.4:
            return (no_of_good_matches, 0.9)
        if percentage >= 0.2:
            return (no_of_good_matches, 0.8)
        if percentage > 0:
            return (no_of_good_matches, 0.7)

        return (no_of_good_matches, 0.0)

    def similar_to(self, other: 'ORB', threshold=0.7) -> float:
        assert(self.descriptors is not None)
        assert(other.descriptors is not None)

        # See: https://stackoverflow.com/a/58098034/5045375
        a = np.array(flatten(self.descriptors))
        b = np.array(flatten(other.descriptors))
        th = threshold

        good_matches = np.count_nonzero(
            lu[(a[:, None, None] ^ b[None, :, None])  # type: ignore
               .view(np.uint8)].sum(2) <= 32 - int(32*th))

        all_possible_matches = len(a) * len(b)

        return ORB.compute_percentage(good_matches, all_possible_matches)[1]
