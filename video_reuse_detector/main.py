from typing import List
from pathlib import Path
from loguru import logger

from video_reuse_detector.fingerprint import Keyframe, \
    FingerprintCollection, produce_fingerprints


def load_keyframes(input_directory: str) -> List[Keyframe]:
    from glob import glob

    keyframes = []

    for f in glob(f'{input_directory}/*.png'):
        logger.debug(f'Loading keyframe from file={f}')
        keyframes.append(Keyframe.from_file(Path(f)))

    return keyframes


def load_fingerprints(input_directory: str) -> List[FingerprintCollection]:
    # TODO: Load audio fingerprints
    keyframes = load_keyframes(input_directory)
    return list(map(FingerprintCollection, keyframes))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Video reuse search tool')

    parser.add_argument(
        'input_video',
        help='The video to compare against the reference set')

    parser.add_argument(
        'reference_set',
        help='A directory containing videos to query against')

    args = parser.parse_args()

    query_prints = produce_fingerprints(Path(args.input_video), Path('foo'))
    reference_fingerprints = load_keyframes(args.reference_set)
