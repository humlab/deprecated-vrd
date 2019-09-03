import numpy as np
import unittest

from video_reuse_detector.color_correlation import color_correlation, RGB


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

    def test_color_correlation(self):
        red = (255, 0, 0)
        image = single_colored_image(16, 16, rgb_color=red)

        self.assertEqual(color_correlation(image)[RGB], 1.0)


if __name__ == '__main__':
    unittest.main()
