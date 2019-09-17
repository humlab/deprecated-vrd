import cv2
import numpy as np

from dataclasses import dataclass
from typing import List

from video_reuse_detector import image_transformation


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
