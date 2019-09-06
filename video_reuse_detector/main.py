import cv2
import numpy as np

from typing import List, Tuple
from pathlib import Path

from video_reuse_detector import video
from video_reuse_detector import fingerprint

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


def extract_frames(segment_id: int,
                   segment: Path,
                   output_directory: Path) -> Tuple[List[np.ndarray],
                                                    List[Path]]:
    frames_dir = output_directory / 'frames'
    frames_output_directory = frames_dir / f'segment{segment_id:03}'
    frame_paths = video.downsample(segment, frames_output_directory)
    frames = [imread(filename) for filename in frame_paths]

    return (frames, frame_paths)


def extract_fingerprints_from_segment(segment_id: int,
                                      segment: Path,
                                      output_directory: Path):
    frames, _ = extract_frames(segment_id, segment, output_directory)
    kf = fingerprint.Keyframe.from_frames(input_video, segment_id, frames)
    th = fingerprint.Thumbnail.from_keyframe(kf)
    cc = fingerprint.ColorCorrelation.from_keyframe(kf)

    return (kf, th, cc)


def store_keyframe(kf: fingerprint.Keyframe, output_directory: Path):
    kf_dir = output_directory / 'keyframes'
    input_video = kf.metadata.video_source
    segment_id = kf.metadata.segment_id

    dst = kf_dir / f'{input_video.stem}-keyframe{segment_id:03}.png'

    imwrite(dst, kf.image)


def store_thumbnail(th: fingerprint.Thumbnail, output_directory: Path):
    thumbs_dir = output_directory / 'thumbs'
    input_video = th.metadata.video_source
    segment_id = th.metadata.segment_id

    dst = thumbs_dir / f'{input_video.stem}-thumb{segment_id:03}.png'

    imwrite(dst, th.image)


def produce_fingerprints(input_video: Path, output_directory: Path):
    # TODO: Produce audio fingerprints, this just creates keyframes
    # TODO: Clean-up intermediary directories
    segments = video.segment(input_video, output_directory / 'segments')

    for segment_id, segment in segments.items():
        kf, th, cc = extract_fingerprints_from_segment(segment_id,
                                                       segment,
                                                       output_directory)

        store_keyframe(kf, output_directory)
        store_thumbnail(th, output_directory)


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
