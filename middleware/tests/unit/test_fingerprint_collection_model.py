import unittest
from pathlib import Path

import numpy as np

from middleware.models.fingerprint_collection import FingerprintCollectionModel
from video_reuse_detector.fingerprint import extract_fingerprint_collection


class FingerprintCollectionModelTest(unittest.TestCase):
    def test_model_conversion(self):
        # TODO: Make it possible to fingerprint a partial video, this is to
        # reduce the number of files we have in our test-directory. I.e., it
        # would be much nicer to have the entire thing stored there and
        # just "slice" out a suitable duration of the video.
        video_path = Path(
            Path.cwd()
            / 'static/tests/videos/panorama_augusti_1944_000030_000040_10s.mp4'
        )  # noqa: E501
        assert video_path.exists()

        root_output_directory = Path.cwd() / "interim"

        fps = extract_fingerprint_collection(video_path, root_output_directory)

        # Convert the fingerprint into our database representation and back
        # again, compare for equality
        fpc = fps[0]
        assert fpc.orb is not None

        model = FingerprintCollectionModel.from_fingerprint_collection(fpc)
        restored = model.to_fingerprint_collection()

        self.assertTrue(np.array_equal(fpc.thumbnail.image, restored.thumbnail.image))

        cc_similarity = fpc.color_correlation.similar_to(restored.color_correlation)
        self.assertTrue(cc_similarity == 1.0)
        self.assertEqual(fpc.video_name, restored.video_name)
        self.assertEqual(fpc.segment_id, restored.segment_id)
        self.assertTrue(fpc.orb.similar_to(restored.orb) > 0.99)
