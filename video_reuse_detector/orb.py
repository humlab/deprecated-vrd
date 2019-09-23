import cv2
import numpy as np

from dataclasses import dataclass
from typing import List, TypeVar

from video_reuse_detector import image_transformation, similarity


T = TypeVar('T')


def flatten(nested_list: List[List[T]]) -> List[T]:
    import itertools

    return list(itertools.chain(*nested_list))


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

    def similar_to(self, other: 'ORB', threshold=0.7) -> float:
        our_descriptors = flatten(self.descriptors)
        their_descriptors = flatten(other.descriptors)

        matches = 0

        for ours in our_descriptors:
            for theirs in their_descriptors:
                sim = 1 - similarity.hamming_distance(ours, theirs)

                if sim > threshold:
                    matches += 1

        number_of_comparisons = len(our_descriptors) * len(their_descriptors)
        percentage = matches/number_of_comparisons

        if percentage >= 0.7:
            return 1.0
        if percentage >= 0.4:
            return 0.9
        if percentage >= 0.2:
            return 0.8
        if percentage > 0:
            return 0.7

        return 0.0
