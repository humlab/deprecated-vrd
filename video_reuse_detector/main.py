import time

from collections import OrderedDict

from loguru import logger
from pathlib import Path
from typing import List, Dict

from video_reuse_detector.fingerprint import FingerprintCollection, \
    FingerprintComparison, compare_fingerprints
from video_reuse_detector.keyframe import Keyframe
import video_reuse_detector.util as util


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
        segment_id = util.segment_id_from_path(path)
        keyframe_image = util.imread(path)

        images[segment_id] = Keyframe(keyframe_image)

    return images


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

    for segment_id, _ in all_comparisons.items():
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
