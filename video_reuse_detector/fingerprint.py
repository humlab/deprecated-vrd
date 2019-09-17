import cv2

from pathlib import Path
from loguru import logger

from video_reuse_detector import downsample, segment
from video_reuse_detector.keyframe import Keyframe

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    import argparse

    parser = argparse.ArgumentParser(
        description='Fingerprint extractor for segment video files')

    parser.add_argument(
        'input_video',
        help='The video segment to extract fingerprints from')

    parser.add_argument(
        'output_directory',
        help='A directory to write the created fingerprints and artefacts to')

    args = parser.parse_args()
    input_video = Path(args.input_video)
    logger.debug(f'Using input_video={input_video} as input')
    segments = segment.segment(input_video, Path(args.output_directory))
    logger.debug(f'Processing segments={segments}')

    keyframes = []

    for s in segments:
        frame_paths = downsample.downsample(s)
        logger.debug(f'Downsampling {s} yielded {frame_paths}')
        frames = list(map(lambda i: cv2.imread(str(i)), frame_paths))
        keyframe = Keyframe.from_frames(frames)
        keyframes.append(keyframe)
