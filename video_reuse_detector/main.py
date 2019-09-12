import numpy as np

from typing import List
from pathlib import Path
from loguru import logger

from video_reuse_detector.fingerprint import Keyframe, \
    FingerprintCollection, Thumbnail


def load_keyframe(file_path: Path) -> Keyframe:
    logger.debug(f'Loading keyframe from file={file_path}')
    return Keyframe.from_file(file_path)


def load_keyframes(input_directory: str) -> List[Keyframe]:
    from glob import glob

    keyframes = []

    for f in glob(f'{input_directory}/*.png'):
        keyframes.append(load_keyframe(Path(f)))

    return keyframes


def load_fingerprints(input_directory: str) -> List[FingerprintCollection]:
    # TODO: Load audio fingerprints
    keyframes = load_keyframes(input_directory)
    return list(map(FingerprintCollection, keyframes))


def normalized_crossed_correlation(qFp: np.ndarray, rFp: np.ndarray) -> float:
    left = qFp - np.mean(qFp)
    right = rFp - np.mean(rFp)
    dividend = np.sum(left*right)
    divisor = np.sqrt(np.sum(left**2) * np.sum(right**2))

    correlation = dividend / divisor

    return correlation


def compare_thumbnails(query: Thumbnail, reference: Thumbnail) -> float:
    return normalized_crossed_correlation(query.image, reference.image)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Video reuse search tool')

    parser.add_argument(
        'input_keyframes',
        help='A directory containing keyframes for our query video')

    parser.add_argument(
        'reference_keyframes',
        help='A directory containing keyframes for our reference video')

    args = parser.parse_args()

    query_prints = load_fingerprints(args.input_keyframes)
    reference_fingerprints = load_fingerprints(args.reference_keyframes)

    logger.debug('Comparing the first pair of thumbnails')
    query = query_prints[0].th
    reference = reference_fingerprints[0].th

    print(compare_thumbnails(query, reference))
