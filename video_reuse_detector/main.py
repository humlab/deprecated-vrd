import numpy as np

from typing import List, TypeVar
from pathlib import Path
from loguru import logger

from video_reuse_detector.fingerprint import Keyframe, \
    FingerprintCollection, Thumbnail, ORB

from video_reuse_detector.fingerprint import ColorCorrelation as CC

import video_reuse_detector


T = TypeVar('T')


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


def compare_color_correlation(query: CC, reference: CC) -> float:
    x = query.as_number
    y = reference.as_number

    return 1.0 - video_reuse_detector.similarity.hamming_distance(x, y)


def flatten(nested_list: List[List[T]]) -> List[T]:
    import itertools

    return list(itertools.chain(*nested_list))


def compare_orb_descriptors(query: ORB, reference: ORB) -> float:
    orb_threshold = 0.7  # p. 81

    query_descriptors = flatten(query.descriptors)
    reference_descriptors = flatten(reference.descriptors)

    assert(len(query_descriptors) == len(reference_descriptors))

    matches = 0

    for i in range(0, len(query_descriptors)):
        query_descriptor = query_descriptors[i]
        reference_descriptor = reference_descriptors[i]

        sim = 1 - video_reuse_detector.similarity.hamming_distance(query_descriptor, reference_descriptor)  # noqa: E501

        if sim > orb_threshold:
            matches += 1

    percentage = matches/len(query_descriptors)

    if percentage >= 0.7:
        return 1.0
    if percentage >= 0.4:
        return 0.9
    if percentage >= 0.2:
        return 0.8
    if percentage > 0:
        return 0.7

    return 0.0


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
    query_th = query_prints[0].th
    reference_th = reference_fingerprints[0].th

    print(compare_thumbnails(query_th, reference_th))

    logger.debug('Comparing the first pair of color correlations')
    query_cc = query_prints[0].cc
    reference_cc = reference_fingerprints[0].cc
    print(compare_color_correlation(query_cc, reference_cc))

    logger.debug('Comparing the first pair of orbs')
    query_orb = query_prints[0].orb
    reference_orb = reference_fingerprints[0].orb
    print(compare_orb_descriptors(query_orb, reference_orb))
