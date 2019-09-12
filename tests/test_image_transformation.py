import numpy as np

from hypothesis import given
from hypothesis.extra.numpy import arrays

import unittest

from video_reuse_detector import image_transformation


class TestImageTransformation(unittest.TestCase):

    @given(image=arrays(np.uint8, shape=(16, 16)))
    def test_fold_preserves_shape(self, image):
        folded = image_transformation.fold(image)
        self.assertEqual(image.shape, folded.shape)


if __name__ == '__main__':
    unittest.main()
