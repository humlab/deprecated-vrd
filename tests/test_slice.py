import unittest
from pathlib import Path

import video_reuse_detector.ffmpeg as ffmpeg


class TestSlice(unittest.TestCase):
    def test_slice(self):
        original = Path(
            Path.cwd()
            / 'static/tests/videos/panorama_augusti_1944_000030_000040_10s.mp4'
        )
        assert original.exists()

        output_directory = Path.cwd() / "interim"
        input_file = ffmpeg.slice(
            original, '00:00:03', '00:00:02', output_directory, overwrite=True
        )
        assert input_file.exists()

        assert int(ffmpeg.get_video_duration(input_file)) == 2
