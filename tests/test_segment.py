import unittest
from pathlib import Path

from video_reuse_detector.ffmpeg import get_video_duration
from video_reuse_detector.segment import segment


class TestSegment(unittest.TestCase):
    def test_segment_default_parameters(self):
        input_file = Path(
            Path.cwd()
            / 'static/tests/videos/panorama_augusti_1944_000030_000040_10s.mp4'
        )
        assert input_file.exists()

        output_directory = Path.cwd() / "interim"
        segment_file_paths = segment(input_file, output_directory)

        # By default, a video that is `S` seconds long is divided into `S` number
        # of segments, meaning that in the default case each second of a given
        # video is treated as its own segment. Hence, we expect that
        # the video duration when rounded up is equal to the number of segments.
        video_duration = get_video_duration(input_file)
        self.assertEqual(int(video_duration), len(segment_file_paths))


if __name__ == '__main__':
    unittest.main()
