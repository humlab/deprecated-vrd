import cv2
import numpy as np

from dataclasses import dataclass
from typing import List, TypeVar, Tuple

from video_reuse_detector import image_transformation, similarity

T = TypeVar('T')


def flatten(nested_list: List[List[T]]) -> List[T]:
    import itertools

    return list(itertools.chain(*nested_list))


# Look-up table for similarity comparison.
# See https://stackoverflow.com/a/58098034/5045375
lu = sum(np.unravel_index(np.arange(256), 8 * (2, )))


@dataclass
class ORB:
    descriptors: List[List[int]]

    @staticmethod
    def from_image(image: np.ndarray) -> 'ORB':
        # TODO: Reminder: call this function using the folded input,
        #       but OpenCV freaks out?
        f_grayscale = image_transformation.grayscale(image)

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
        # TODO: the remark in the paper refers to the number of features
        #       on average remove this but make it into a separate commit
        orb = cv2.ORB_create(nfeatures=250, scoreType=cv2.ORB_FAST_SCORE)

        # find the keypoints with ORB
        _, des = orb.detectAndCompute(f_grayscale, None)

        if des is None:
            des = []  # No features found

        return ORB(des)

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

    def similar_to_lu(self, other: 'ORB', threshold=0.7) -> Tuple[int, float]:
        # See: https://stackoverflow.com/a/58098034/5045375
        a = np.array(flatten(self.descriptors))
        b = np.array(flatten(other.descriptors))
        th = threshold

        good_matches = np.count_nonzero(
            lu[(a[:, None, None] ^ b[None, :, None])
               .view(np.uint8)].sum(2) <= 32 - int(32*th))

        all_possible_matches = len(a) * len(b)

        return ORB.compute_percentage(good_matches, all_possible_matches)

    def similar_to(self, other: 'ORB', threshold=0.7) -> float:
        return self.similar_to_lu(other)[1]

    def similar_to_naive(self, other: 'ORB', threshold=0.7) -> Tuple[int, float]:  # noqa: E501
        our_descriptors = flatten(self.descriptors)
        their_descriptors = flatten(other.descriptors)

        good_matches = 0

        for ours in our_descriptors:
            for theirs in their_descriptors:
                sim = 1 - similarity.hamming_distance(ours, theirs)

                if sim >= threshold:
                    good_matches += 1

        all_possible_matches = len(our_descriptors) * len(their_descriptors)
        return ORB.compute_percentage(good_matches, all_possible_matches)
