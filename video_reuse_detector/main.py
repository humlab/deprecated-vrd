import cv2
import video

from pathlib import Path

import fingerprint

"""
This code implements the fingerprinting method proposed by Zobeida Jezabel
Guzman-Zavaleta in the thesis "An Effective and Efficient Fingerprinting Method
for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis,
specifically from the section 5.4 Discussion, where the author details the
parameter values that "proved" the "best" during her experiments.
"""


def imread(filename: Path):
    return cv2.imread(str(filename))


def imwrite(filename: Path, image):
    filename.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(filename), image)


def produce_fingerprints(input_video: Path, output_directory: Path):
    # TODO: Produce audio fingerprints, this just creates keyframes
    # TODO: Clean-up intermediary directories
    segments_dir = output_directory / 'segments'
    frames_dir = output_directory / 'frames'
    segments = video.segment(input_video, segments_dir)

    for segment_id, segment in segments.items():
        frames_output_directory = frames_dir / f'segment{segment_id:03}'
        frame_paths = video.downsample(segment, frames_output_directory)
        frames = [imread(filename) for filename in frame_paths]

        kf_dir = output_directory / 'keyframes'
        kf = fingerprint.Keyframe.from_frames(input_video, segment_id, frames)

        imwrite(kf_dir / f'{input_video.stem}-keyframe{segment_id:03}.png', kf.image)  # noqa: E501

        thumbs_dir = output_directory / 'thumbs'
        thumb = fingerprint.Thumbnail.from_keyframe(kf)
        imwrite(thumbs_dir / f'{input_video.stem}-thumb{segment_id:03}.png', thumb.image)  # noqa: E501


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    import argparse

    parser = argparse.ArgumentParser(
        description='Fingerprint extractor for video files')

    parser.add_argument(
        'input_video',
        help='The video to extract fingerprints from')

    parser.add_argument(
        'output_directory',
        help='A directory to write the created fingerprints and artefacts to')

    args = parser.parse_args()
    input_video = Path(args.input_video)
    produce_fingerprints(input_video, Path(args.output_directory))
