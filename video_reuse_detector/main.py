import cv2
import numpy as np

from dataclasses import dataclass

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
    cv2_friendly_paths = map(str, list_keyframe_paths(directory))
    images = list(map(cv2.imread, cv2_friendly_paths))
    return list(map(Keyframe, images))


def is_color_image(image: np.ndarray) -> bool:
    return len(image.shape) == 3


def is_grayscale_image(image: np.ndarray) -> bool:
    return len(image.shape) < 3


@dataclass
class FingerprintCollection:
    keyframe: Keyframe
    thumbnail: Thumbnail
    color_correlation: ColorCorrelation
    orb: ORB
    video_id: str

    # TODO: Add SSM

    @staticmethod
    def from_keyframe(keyframe: Keyframe, video_id: str) -> 'FingerprintCollection':  # noqa: E501
        # Heuristically, it will be necessary to compute all fingerprints
        # when comparing two videos as the multi-level matching algorithm
        # is traversed and doing so here, as opposed to within the logic
        # for establishing a similarity value proves more succinct.
        keyframe = keyframe
        thumbnail = Thumbnail.from_image(keyframe.image)

        if is_color_image(keyframe.image):
            color_correlation = ColorCorrelation.from_image(keyframe.image)
        else:
            color_correlation = None

        # TODO: Use folded variant here
        orb = ORB.from_image(keyframe.image)
        if (len(orb.descriptors) == 0):
            orb = None

        # TODO: set SSM

        return FingerprintCollection(keyframe, thumbnail, color_correlation, orb, video_id)  # noqa: E501


def compare_thumbnails(query: FingerprintCollection,
                       reference: FingerprintCollection,
                       similarity_threshold=0.65) -> Tuple[bool,
                                                           float]:
    S_th = query.thumbnail.similar_to(reference.thumbnail)
    return (S_th >= similarity_threshold, S_th)


# Could be compared, threshold exceeded, similarity score
def compare_color_correlation(query: FingerprintCollection,
                              reference: FingerprintCollection,
                              similarity_threshold=0.65) -> Tuple[bool,
                                                                  bool,
                                                                  float]:
    COULD_NOT_COMPARE = (False, False, 0)
    if query.color_correlation is None:
        # TODO: Include id
        logger.debug('Could not compare CC because query image is in grayscale')  # noqa: E501
        return COULD_NOT_COMPARE

    if reference.color_correlation is None:
        # TODO: Include id
        logger.debug('Could not compare CC because reference image is in grayscale')  # noqa: E501
        return COULD_NOT_COMPARE

    S_cc = query.color_correlation.similar_to(reference.color_correlation)

    return (True, S_cc >= similarity_threshold, S_cc)


def compare_orb(query, reference, similarity_threshold=0.7):
    COULD_NOT_COMPARE = (False, False, 0.0)

    if query.orb is None:
        logger.debug('No orb descriptors found for query image')
        return COULD_NOT_COMPARE

    if reference.orb is None:
        logger.debug('No orb descriptors found for reference image')
        return COULD_NOT_COMPARE

    S_orb = query.orb.similar_to(reference.orb)
    return (True, S_orb >= similarity_threshold, S_orb)


def compare_fingerprints(query: FingerprintCollection, reference: FingerprintCollection):  # noqa: E501
    similar_enough, S_th = compare_thumbnails(query, reference)

    if similar_enough:
        compare_cc = compare_color_correlation
        could_compare, similar_enough, S_cc = compare_cc(query, reference)

        if could_compare and similar_enough:
            could_compare, similar_enough, S_orb = compare_orb(query, reference)  # noqa: E501

            if could_compare and similar_enough:
                # Level A, visual fingerprints matched. Not processing audio
                w_th, w_cc, w_orb = 0.4, 0.3, 0.3
                similarity = w_th*S_th + w_cc*S_cc + w_orb*S_orb
                return similarity
            else:
                return 0  # Extract SSM, if SSM matches -> Level B, else Level C # noqa: E501
        else:
            could_compare, similar_enough, S_orb = compare_orb(query, reference)  # noqa: E501

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
        query_fingerprints_directory: Path,
        reference_fingerprints_directory: Path):
    query_keyframes = load_keyframes(query_fingerprints_directory)
    query_video_name = query_fingerprints_directory.stem
    query_fps = list(map(lambda keyframe: FingerprintCollection.from_keyframe(keyframe, query_video_name), query_keyframes))  # noqa: E501

    reference_keyframes = load_keyframes(reference_fingerprints_directory)
    reference_video_name = reference_fingerprints_directory.stem
    reference_fps = list(map(lambda keyframe: FingerprintCollection.from_keyframe(keyframe, reference_video_name), reference_keyframes))  # noqa: E501

    for query_fp in query_fps:
        for reference_fp in reference_fps:
            print(compare_fingerprints(query_fp, reference_fp))


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
    compute_similarity_between(query_directory, reference_directory)
