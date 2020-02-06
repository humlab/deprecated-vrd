import math
import unittest
from pathlib import Path

import video_reuse_detector.ffmpeg as ffmpeg
from video_reuse_detector.segment import segment


class TestSegment(unittest.TestCase):
    def test_segment_default_parameters(self):
        original = Path(Path.cwd() / 'static/videos/archive/panorama_augusti_1944.mp4')
        assert original.exists()

        output_directory = Path.cwd() / "interim"
        input_file = ffmpeg.slice(original, '00:00:30', '00:00:02', output_directory)
        assert input_file.exists()

        segment_file_paths = segment(input_file, output_directory)

        # By default, a video that is `S` seconds long is divided into `S` number
        # of segments, meaning that in the default case each second of a given
        # video is treated as its own segment. Hence, we expect that
        # the video duration when rounded up is equal to the number of segments.
        video_duration = ffmpeg.get_video_duration(input_file)
        self.assertEqual(math.ceil(video_duration), len(segment_file_paths))


if __name__ == '__main__':
    unittest.main()
