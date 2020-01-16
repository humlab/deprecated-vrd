import unittest
from pathlib import Path

from video_reuse_detector.downsample import downsample
from video_reuse_detector.segment import segment


class TestDownsample(unittest.TestCase):
    def test_downsample_default_parameters(self):
        input_file = Path(
            Path.cwd()
            / 'static/tests/videos/panorama_augusti_1944_000030_000040_10s.mp4'
        )
        assert input_file.exists()

        output_directory = Path.cwd() / "interim"
        segment_file_paths = segment(input_file, output_directory)

        extracted_frames = downsample(segment_file_paths[0])

        # The default number of frames extracted should be 5
        self.assertEqual(len(extracted_frames), 5)


if __name__ == '__main__':
    unittest.main()
