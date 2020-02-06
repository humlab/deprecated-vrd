import unittest
from pathlib import Path

import video_reuse_detector.ffmpeg as ffmpeg
from video_reuse_detector.downsample import downsample
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.segment import segment


class TestKeyframe(unittest.TestCase):
    def test_keyframe_creation(self):
        original = Path(Path.cwd() / 'static/videos/archive/panorama_augusti_1944.mp4')
        assert original.exists()

        output_directory = Path.cwd() / "interim"
        input_file = ffmpeg.slice(original, '00:00:30', '00:00:02', output_directory)
        assert input_file.exists()

        segment_file_paths = segment(input_file, output_directory)

        extracted_frames = downsample(segment_file_paths[0])
        keyframe_image = Keyframe.from_frame_paths(extracted_frames).image

        self.assertEqual(keyframe_image.shape[0:2], (Keyframe.height, Keyframe.width))


if __name__ == '__main__':
    unittest.main()
