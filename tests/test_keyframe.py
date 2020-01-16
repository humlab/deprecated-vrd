import unittest
from pathlib import Path

from video_reuse_detector.downsample import downsample
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.segment import segment


class TestKeyframe(unittest.TestCase):
    def test_keyframe_creation(self):
        input_file = Path(
            Path.cwd()
            / 'static/tests/videos/panorama_augusti_1944_000030_000040_10s.mp4'
        )
        assert input_file.exists()

        output_directory = Path.cwd() / "interim"
        segment_file_paths = segment(input_file, output_directory)

        extracted_frames = downsample(segment_file_paths[0])
        keyframe_image = Keyframe.from_frame_paths(extracted_frames).image

        self.assertEqual(keyframe_image.shape[0:2], (Keyframe.height, Keyframe.width))


if __name__ == '__main__':
    unittest.main()
