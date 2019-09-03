import numpy as np
from hypothesis import given
from hypothesis.extra.numpy import arrays

import unittest

from video_reuse_detector.color_correlation import color_correlation, RGB, \
    correlation_cases


def single_colored_image(width, height, rgb_color=(0, 0, 0)):
    """
    Create new image(numpy array) filled with certain color in RGB where
    the tuple values are expected to range from 0..255

    Code courtesy of https://stackoverflow.com/a/22920965/5045375
    """
    number_of_color_channels = 3  # BGR!
    image = np.zeros((height, width, number_of_color_channels), np.uint8)

    # RGB (the world) -> BGR (OpenCV)
    color = tuple(reversed(rgb_color))
    image[:] = color  # Fill image with color

    return image


class TestColorCorrelation(unittest.TestCase):

    def test_color_correlation_black_image(self):
        # This set-up triggered a ZeroDivisionError, this would happen for any
        # image where r == g == b throughout an entire block which could happen
        # for very bright or very dark scenes
        black = (0, 0, 0)
        image = single_colored_image(16, 16, rgb_color=black)

        # No correlation case was triggered
        cc = color_correlation(image)
        for (_, percentage) in cc.items():
            self.assertEqual(percentage, 0)

    def test_color_correlation_red(self):
        red = (255, 0, 0)
        image = single_colored_image(16, 16, rgb_color=red)

        # The correlation case r >= g >= b is triggered for every pixel in
        # the image,
        self.assertEqual(color_correlation(image)[RGB], 1.0)

    @given(image=arrays(np.uint8, shape=(16, 16, 3)))
    def test_color_correlation_fixed_number_of_cases(self, image):
        self.assertEqual(len(color_correlation(image)), len(correlation_cases))


if __name__ == '__main__':
    unittest.main()
