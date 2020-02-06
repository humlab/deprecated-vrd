import math
import unittest
from pathlib import Path

import video_reuse_detector.ffmpeg as ffmpeg
from video_reuse_detector.fingerprint import (
    FingerprintComparison,
    extract_fingerprint_collection,
)


class TestFingerprintComparison(unittest.TestCase):
    def test_comparison(self):
        output_directory = Path.cwd() / "interim"

        reference_video_path = Path(
            Path.cwd() / 'static/videos/archive/panorama_augusti_1944.mp4'
        )
        assert reference_video_path.exists()

        reference_video_path = ffmpeg.slice(
            reference_video_path, '00:00:30', '00:00:02', output_directory
        )

        query_video_path = ffmpeg.softglow(reference_video_path, output_directory)
        assert query_video_path.exists()

        query_fps = extract_fingerprint_collection(query_video_path, output_directory)
        reference_fps = extract_fingerprint_collection(
            reference_video_path, output_directory
        )

        sorted_comparisons = FingerprintComparison.compare_all(query_fps, reference_fps)

        query_video_duration = ffmpeg.get_video_duration(query_video_path)

        # sorted_comparison is a mapping of segment ids in the query video
        # and so the number of elements should be equal to the length of the
        # video given the default segment behaviour is to segment each second
        #
        # Notice how ceil is used here. For certain videos, their length is
        # fractional. Say, 10.12 seconds. If so, there'll be 11 segments. If
        # the fractional component is sufficiently small, for instance,
        # 10.008000 then only 10 segments are extracted.
        self.assertEqual(
            math.ceil(query_video_duration), len(sorted_comparisons.keys())
        )

        # For any valid segment identifier `id` in the query video,
        # sorted_comparison[id] is a list containing a fingerprint comparison
        # object describing the relation between the a segment in the reference
        # video and the query video. sorted_comparison[id] should contain as
        # many elements as the reference video is long, again as a consequence
        # of the default segmenting behaviour.
        reference_video_duration = ffmpeg.get_video_duration(reference_video_path)

        def is_as_long_as_reference_video(l):
            return len(l) == math.ceil(reference_video_duration)

        self.assertTrue(
            all(is_as_long_as_reference_video(l) for l in sorted_comparisons.values())
        )


if __name__ == '__main__':
    unittest.main()
