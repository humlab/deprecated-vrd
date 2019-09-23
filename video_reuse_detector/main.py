import cv2
import numpy as np

from loguru import logger
from pathlib import Path
from typing import List, Tuple

from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.thumbnail import Thumbnail
from video_reuse_detector.color_correlation import ColorCorrelation
from video_reuse_detector.orb import ORB


def list_keyframe_paths(
        directory: Path,
        glob_pattern: str = '**/keyframe.png') -> List[Path]:
    keyframe_paths = list(directory.glob(glob_pattern))

    logger.debug(f'Found {len(keyframe_paths)} keyframes under "{directory}" (glob_pattern="{glob_pattern}")')  # noqa: E501
    return keyframe_paths


def load_keyframes(directory: Path) -> List[Keyframe]:
    return list(map(cv2.imread, list_keyframe_paths(directory)))


def is_color_image(image: np.ndarray) -> bool:
    return len(image.shape) == 3


def is_grayscale_image(image: np.ndarray) -> bool:
    return len(image.shape) < 3


def compare_thumbnails(query_thumbnail: Thumbnail,
                       reference_thumbnail: Thumbnail,
                       similarity_threshold=0.65) -> Tuple[bool,
                                                           float]:
    S_th = query_thumbnail.similar_to(reference_thumbnail)
    return (S_th >= similarity_threshold, S_th)


# Could be compared, threshold exceeded, similarity score
def compare_color_correlation(query_keyframe: Keyframe,
                              reference_keyframe: Keyframe,
                              similarity_threshold=0.65) -> Tuple[bool,
                                                                  bool,
                                                                  float]:
    query_image = query_keyframe.image
    reference_image = reference_keyframe.image
    COULD_NOT_COMPARE = (False, False, 0.0)

    if is_grayscale_image(query_image):
        # TODO: Include id
        logger.debug('Could not compare CC because query image is in grayscale')  # noqa: E501
        return COULD_NOT_COMPARE

    if is_grayscale_image(reference_image):
        # TODO: Include id
        logger.debug('Could not compare CC because reference image is in grayscale')  # noqa: E501
        return COULD_NOT_COMPARE

    query_cc = ColorCorrelation.from_image(query_keyframe.image)
    reference_cc = ColorCorrelation.from_image(reference_keyframe.image)

    S_cc = query_cc.similar_to(reference_cc)

    return (True, S_cc >= similarity_threshold, S_cc)


def compare_orb(query_keyframe, reference_keyframe, similarity_threshold=0.7):
    # TODO: Apply on folded keyframes
    query_orb = ORB.from_image(query_keyframe.image)
    COULD_NOT_COMPARE = (False, False, 0.0)

    if len(query_orb.descriptors) == 0:
        logger.debug('No orb descriptors found for query image')
        return COULD_NOT_COMPARE

    reference_orb = ORB.from_image(reference_keyframe.image)
    if len(reference_orb.descriptors) == 0:
        logger.debug('No orb descriptors found for reference image')
        return COULD_NOT_COMPARE

    S_orb = query_orb.similar_to(reference_orb)
    return (True, S_orb >= similarity_threshold, S_orb)


def compare_keyframes(query_keyframe: Keyframe, reference_keyframe: Keyframe):
    query_th = Thumbnail.from_image(query_keyframe.image)
    reference_th = Thumbnail.from_image(reference_keyframe.image)

    similar_enough, S_th = compare_thumbnails(query_th, reference_th)

    if similar_enough:
        compare_cc = compare_color_correlation
        could_compare, similar_enough, S_cc = compare_cc(query_keyframe, reference_keyframe)  # noqa: E501

        if could_compare and similar_enough:
            could_compare, similar_enough, S_orb = compare_orb(query_keyframe, reference_keyframe)  # noqa: E501

            if could_compare and similar_enough:
                # Level A, visual fingerprints matched. Not processing audio
                w_th, w_cc, w_orb = 0.4, 0.3, 0.3
                similarity = w_th*S_th + w_cc*S_cc + w_orb*S_orb
                return similarity
            else:
                return 0  # Extract SSM, if SSM matches -> Level B, else Level C # noqa: E501
        else:
            could_compare, similar_enough, S_orb = compare_orb(query_keyframe, reference_keyframe)  # noqa: E501

            if could_compare and similar_enough:
                # Level D, video is in grayscale and local keypoints matched
                w_th, w_orb = 0.6, 0.4
                similarity = w_th*S_th + w_orb*S_orb
                return similarity
            else:
                return 0  # Extract SSM, if SSM matches -> Level E, otherwise Level F (th match) # noqa: E501
    else:
        return 0


def compute_similarity_between(
        query_fingerprint_directory,
        reference_fingerprints_directory):
    # TODO: Do not recompute FPs for the query video
    # TODO: Lazily load reference FPs into a cache?
    query_keyframes = load_keyframes(query_fingerprint_directory)
    reference_keyframes = load_keyframes(reference_fingerprints_directory)

    for query_keyframe in query_keyframes:
        for reference_keyframe in reference_keyframes:
            compare_keyframes(query_keyframe, reference_keyframe)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Video reuse detector')

    parser.add_argument(
        'query_fingerprints_directory',
        help='A directory with fingerprints')

    parser.add_argument(
        'reference_fingerprints_directory',
        help='Another directory with fingerprints')

    args = parser.parse_args()

    query_directory = Path(args.query_fingerprints_directory)
    logger.debug(f'Treating "{query_directory}" as the query "video"')

    reference_directory = Path(args.reference_fingerprints_directory)
    logger.debug(f'Treating "{reference_directory}" as the reference "video"')
