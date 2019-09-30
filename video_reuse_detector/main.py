import cv2
import numpy as np
import time

from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, auto

from loguru import logger
from pathlib import Path
from typing import List, Tuple, Dict

from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.thumbnail import Thumbnail
from video_reuse_detector.color_correlation import ColorCorrelation
from video_reuse_detector.orb import ORB


def timeit(func):

    def measure_elapsed_time(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug("Function '{}' executed in {:f} s", func.__name__, end - start)  # noqa: E501
        return result

    return measure_elapsed_time


def list_keyframe_paths(
        directory: Path,
        glob_pattern: str = '**/keyframe.png') -> List[Path]:
    keyframe_paths = list(directory.glob(glob_pattern))

    logger.debug(f'Found {len(keyframe_paths)} keyframes under "{directory}" (glob_pattern="{glob_pattern}")')  # noqa: E501
    return keyframe_paths


# segment_id -> keyframe
def load_keyframes(directory: Path) -> Dict[int, Keyframe]:
    images = {}

    for path in list_keyframe_paths(directory):
        # For a path on the form,
        #
        # /some/path/to/videoname/segment/000/keyframe.png
        #
        # then path.parents[0] is
        #
        # /some/path/to/videoname/segment/000
        #
        # and path.parents[0].stem is "000"
        segment_id = int(str(path.parents[0].stem))

        # imread cannot be applied to a Path object
        cv2_friendly_path = str(path)
        keyframe_image = cv2.imread(cv2_friendly_path)

        images[segment_id] = Keyframe(keyframe_image)

    return images


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
    segment_id: int

    # TODO: Add SSM

    @staticmethod
    def from_keyframe(keyframe: Keyframe, video_id: str, segment_id: int) -> 'FingerprintCollection':  # noqa: E501
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

        orb = ORB.from_image(keyframe.image)
        if (len(orb.descriptors) == 0):
            orb = None

        # TODO: set SSM

        return FingerprintCollection(keyframe, thumbnail, color_correlation, orb, video_id, segment_id)  # noqa: E501


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
        logger.debug(f'No orb descriptors found for query image with segment_id={query.segment_id}')  # noqa: E501
        return COULD_NOT_COMPARE

    if reference.orb is None:
        logger.debug(f'No orb descriptors found for reference image with segment_id={reference.segment_id}')  # noqa: E501
        return COULD_NOT_COMPARE

    S_orb = query.orb.similar_to(reference.orb)
    return (True, S_orb >= similarity_threshold, S_orb)


class MatchLevel(Enum):
    LEVEL_A = auto()
    LEVEL_B = auto()
    LEVEL_C = auto()
    LEVEL_D = auto()
    LEVEL_F = auto()
    LEVEL_G = auto()


def compare_ssm(
        query: FingerprintCollection,
        reference: FingerprintCollection) -> Tuple[bool, bool, float]:
    return False, False, 0


@dataclass
class FingerprintComparison:
    query_segment_id: int
    reference_segment_id: int
    level: MatchLevel
    similarity: float


def __compare_fingerprints__(
        query: FingerprintCollection,
        reference: FingerprintCollection) -> Tuple[MatchLevel,
                                                   float]:

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
                return (MatchLevel.LEVEL_A, similarity)
            else:
                could_compare, similar_enough, S_ssm = compare_ssm(query, reference)  # noqa: E501
                if could_compare and similar_enough:
                    # Level B
                    w_th, w_cc, w_ssm = 0.4, 0.3, 0.2
                    similarity = w_th*S_th + w_cc*S_cc + w_ssm*S_ssm
                    return (MatchLevel.LEVEL_B, similarity)
                else:
                    w_th, w_cc = 0.5, 0.3
                    similarity = w_th*S_th + w_cc*S_cc
                    return (MatchLevel.LEVEL_C, similarity)
        else:
            could_compare, similar_enough, S_orb = compare_orb(query, reference)  # noqa: E501

            if could_compare and similar_enough:
                # Level D, video is in grayscale and local keypoints matched
                w_th, w_orb = 0.6, 0.4
                similarity = w_th*S_th + w_orb*S_orb
                return (MatchLevel.LEVEL_D, similarity)
            else:
                could_compare, similar_enough, S_ssm = compare_ssm(query, reference)  # noqa: E501
                if could_compare and similar_enough:
                    w_th, w_ssm = 0.5, 0.2
                    similarity = w_th*S_th + w_ssm*S_ssm
                    return (MatchLevel.LEVEL_B, similarity)
                else:
                    w_th = 0.5  # TODO: What should the weight here be?
                    similarity = w_th*S_th
                    return (MatchLevel.LEVEL_F, similarity)
    else:
        # Thumbnails too dissimilar to continue comparing
        return (MatchLevel.LEVEL_G, 0)


def compare_fingerprints(
        query: FingerprintCollection,
        reference: FingerprintCollection) -> FingerprintComparison:
    comparison = __compare_fingerprints__(query, reference)

    return FingerprintComparison(query.segment_id,
                                 reference.segment_id,
                                 comparison[0],
                                 comparison[1])


def fingerprint_collection_from_directory(directory: Path):
    keyframes = load_keyframes(directory)
    video_id = directory.stem
    fingerprints = []

    for segment_id, keyframe in keyframes.items():
        fp = FingerprintCollection.from_keyframe(keyframe, video_id, segment_id)  # noqa: E501
        fingerprints.append(fp)

    return fingerprints


@timeit
def compute_similarity_between(
        query_fingerprints_directory: Path,
        reference_fingerprints_directory: Path):
    query_fps = fingerprint_collection_from_directory(query_fingerprints_directory)  # noqa: E501
    reference_fps = fingerprint_collection_from_directory(reference_fingerprints_directory)  # noqa: E501

    # Map from the segment id in the query video to a list of
    # tuples containing the reference segment id and the return
    # value of the fingerprint comparison
    all_comparisons = {query_fp.segment_id: [] for query_fp in query_fps}  # type: Dict[int, List[FingerprintComparison]]  # noqa: E501

    # sort by segment_id in the keys (0, 1, ...)
    all_comparisons = OrderedDict(sorted(all_comparisons.items()))

    for query_fp in query_fps:
        for reference_fp in reference_fps:
            logger.trace(f'Comparing {query_fp.video_id}:{query_fp.segment_id} to {reference_fp.video_id}:{reference_fp.segment_id}')  # noqa: E501

            comparison = compare_fingerprints(query_fp, reference_fp)
            all_comparisons[query_fp.segment_id].append(comparison)

    for segment_id, comparisons in all_comparisons.items():
        # Sort by the similarity score, making the highest similarity
        # items be listed first, i.e. 1.0 goes before 0.5
        comparison_similarity = lambda comparison: comparison.similarity  # noqa: E731, E501

        all_comparisons[segment_id] = sorted(all_comparisons[segment_id],
                                             key=comparison_similarity,
                                             reverse=True)

    return all_comparisons


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

    similarities = compute_similarity_between(query_directory,
                                              reference_directory)

    for segment_id, sorted_comparisons in similarities.items():
        id_to_similarity_score_tuples = [(c.reference_segment_id, c.similarity) for c in sorted_comparisons]  # noqa: E501
        print(segment_id, id_to_similarity_score_tuples[:5])
