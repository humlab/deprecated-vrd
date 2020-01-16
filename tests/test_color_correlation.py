import os
import unittest

import cv2
import numpy as np
from hypothesis import given
from hypothesis.extra.numpy import arrays
from hypothesis.strategies import floats, integers

from video_reuse_detector.color_correlation import (
    CORRELATION_CASES,
    RGB,
    ColorCorrelation,
    avg_intensity_per_color_channel,
    normalized_color_correlation_histogram,
    trunc,
)


def rgb(bgr):
    return tuple(reversed(bgr))


def bgr(rgb):
    return tuple(reversed(rgb))


def single_colored_image(width, height, rgb_color=(0, 0, 0)):
    """
    Create new image(numpy array) filled with certain color in RGB where
    the tuple values are expected to range from 0..255

    Code courtesy of https://stackoverflow.com/a/22920965/5045375
    """
    number_of_color_channels = 3  # BGR!
    image = np.zeros((height, width, number_of_color_channels), np.uint8)

    # RGB (the world) -> BGR (OpenCV)
    color = bgr(rgb_color)
    image[:] = color  # Fill image with color

    return image


def number_of_decimals(f):
    decimal_count = str(f)[::-1].find('.')

    # decimal_count is -1 if there are no decimals at all
    return decimal_count if decimal_count != -1 else 0


def load_opencv_image(image_name: str, flags=None) -> np.ndarray:
    if flags is None:
        flags = cv2.IMREAD_COLOR

    return cv2.imread(cv2.samples.findFile(image_name), flags)


def load_rubberwhale1(flags=None) -> np.ndarray:
    return load_opencv_image('rubberwhale1.png', flags)


def load_rubberwhale2(flags=None) -> np.ndarray:
    return load_opencv_image('rubberwhale2.png', flags)


class TestColorCorrelation(unittest.TestCase):
    def setUp(self):
        # The images used in the tests can be found here
        #
        # https://github.com/opencv/opencv/tree/master/samples/data
        #
        # clone the opencv repository and add the samples/data dir to your env
        # or use make opencv in the project root
        cv2.samples.addSamplesDataSearchPath(os.environ['OPEN_CV_SAMPLES'])

    def test_color_correlation_histogram_black_image(self):
        # This set-up triggered a ZeroDivisionError, this would happen for any
        # image where r == g == b throughout an entire block which could happen
        # for very bright or very dark scenes
        black = (0, 0, 0)
        image = single_colored_image(16, 16, rgb_color=black)

        # No correlation case was triggered
        cc = normalized_color_correlation_histogram(image)
        for (_, percentage) in cc.items():
            self.assertEqual(percentage, 0)

    def test_color_correlation_histogram_red(self):
        red = (255, 0, 0)
        image = single_colored_image(16, 16, rgb_color=red)

        # The correlation case r >= g >= b is triggered for every pixel in
        # the image,
        cc = normalized_color_correlation_histogram(image)
        self.assertEqual(cc[RGB], 1.0)

    def test_avg_intensity_per_color_channel_single_colored_image(self):
        red = (255, 0, 0)
        image = single_colored_image(16, 16, rgb_color=red)

        self.assertEqual(rgb(avg_intensity_per_color_channel(image)), red)

    def test_avg_intensity_per_color_channel_two_colors(self):
        red = (255, 0, 0)
        blue = (0, 0, 255)
        image = np.array([[red, blue], [blue, red]])
        actual = rgb(avg_intensity_per_color_channel(image))
        expected = (255 / 2, 0, 255 / 2)

        self.assertEqual(actual, expected)

    def test_color_correlation_histogram_idempotency(self):
        whale1 = load_rubberwhale1()

        cc1 = ColorCorrelation.from_image(whale1)

        # Invoking the method on whale1 again is intentional
        cc2 = ColorCorrelation.from_image(whale1)

        self.assertEqual(cc1, cc2)

    def test_color_correlation_histogram_values_sum_to_100(self):
        whale1 = load_rubberwhale1()

        cc1 = ColorCorrelation.from_image(whale1)
        self.assertEqual(sum(cc1.histogram.values()), 100)

    def test_that_an_image_cc_histogram_is_always_similar_to_itself(self):
        whale1 = load_rubberwhale1()
        cc1 = ColorCorrelation.from_image(whale1)

        # Invoking the method on whale1 again is intentional
        cc2 = ColorCorrelation.from_image(whale1)

        self.assertTrue(cc1.similar_to(cc2) == 1.0)

    def test_color_correlation_histogram_can_be_recreated_from_encoding(self):
        whale1 = load_rubberwhale1()

        cc1 = ColorCorrelation.from_image(whale1)
        encoded = cc1.as_number
        cc2 = ColorCorrelation.from_number(encoded)

        # The new CC encodes the same
        self.assertEqual(cc2.as_number, encoded)

        # And the two CCs are equal
        self.assertEqual(cc1, cc2)

    def test_two_similar_images_have_histograms_that_are_very_similar(self):
        whale1 = load_rubberwhale1()
        whale2 = load_rubberwhale2()

        cc1 = ColorCorrelation.from_image(whale1)
        cc2 = ColorCorrelation.from_image(whale2)

        # The two histograms are distinct,
        self.assertNotEqual(cc1.histogram, cc2.histogram)

        # But the ColorCorrelations are similar!
        # In fact, these two correlations are very similar,
        self.assertTrue(cc1.similar_to(cc2) > 0.9)

    def test_color_correlation_histogram_grayscale(self):
        whale1 = load_rubberwhale1(cv2.IMREAD_GRAYSCALE)
        assert len(whale1.shape) < 3

        with self.assertRaises(ValueError):
            ColorCorrelation.from_image(whale1)

    @given(image=arrays(np.uint8, shape=(16, 16, 3)))
    def test_color_correlation_histogram_fixed_number_of_cases(self, image):
        actual = len(normalized_color_correlation_histogram(image))
        expected = len(CORRELATION_CASES)

        self.assertEqual(actual, expected)

    def test_trunc_yields_two_decimals_for_number_with_three_decimals(self):
        f = 0.524
        assert number_of_decimals(f) == 3

        self.assertEqual(number_of_decimals(trunc(f)), 2)

    def test_trunc_yields_two_decimals_for_number_with_two_decimals(self):
        f = 0.52
        assert number_of_decimals(f) == 2

        self.assertEqual(number_of_decimals(trunc(f)), 2)

    @given(
        f=floats(min_value=0.0, max_value=1.0),
        no_of_decimals=integers(min_value=1, max_value=31),
    )
    def test_trunc(self, f, no_of_decimals):
        truncated_number = trunc(f, no_of_decimals)

        self.assertTrue(number_of_decimals(truncated_number) <= no_of_decimals)


if __name__ == '__main__':
    unittest.main()
