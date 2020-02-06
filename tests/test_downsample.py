import unittest
from pathlib import Path

import video_reuse_detector.ffmpeg as ffmpeg
from video_reuse_detector.downsample import downsample
from video_reuse_detector.segment import segment


class TestDownsample(unittest.TestCase):
    def test_downsample_default_parameters(self):
        original = Path(Path.cwd() / 'static/videos/archive/panorama_augusti_1944.mp4')
        assert original.exists()

        output_directory = Path.cwd() / "interim"
        input_file = ffmpeg.slice(original, '00:00:30', '00:00:02', output_directory)
        assert input_file.exists()

        segment_file_paths = segment(input_file, output_directory)

        extracted_frames = downsample(segment_file_paths[0])

        # FIXME: The default number of frames extracted should be 5, or 6. Which
        # is dependent on ffmpeg. See http://ffmpeg.org/ffmpeg-filters.html#fps
        self.assertTrue(len(extracted_frames) == 5 or len(extracted_frames) == 6)


if __name__ == '__main__':
    unittest.main()
