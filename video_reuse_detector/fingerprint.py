from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from loguru import logger

import video_reuse_detector.util as util
from video_reuse_detector.color_correlation import ColorCorrelation
from video_reuse_detector.downsample import downsample
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.orb import ORB
from video_reuse_detector.segment import segment
from video_reuse_detector.thumbnail import Thumbnail


class MatchLevel(Enum):
    LEVEL_A = auto()
    LEVEL_B = auto()
    LEVEL_C = auto()
    LEVEL_D = auto()
    LEVEL_F = auto()
    LEVEL_G = auto()


def is_color_image(image: np.ndarray) -> bool:
    return len(image.shape) == 3


def is_grayscale_image(image: np.ndarray) -> bool:
    return len(image.shape) < 3


@dataclass
class FingerprintCollection:
    thumbnail: Thumbnail
    color_correlation: ColorCorrelation
    orb: ORB
    video_name: str
    segment_id: int

    # TODO: Add SSM? Will we support audio?

    @staticmethod
    def from_keyframe(
        keyframe: Keyframe, video_name: str, segment_id: int
    ) -> 'FingerprintCollection':  # noqa: E501
        # Heuristically, it will be necessary to compute all fingerprints
        # when comparing two videos as the multi-level matching algorithm
        # is traversed and doing so here, as opposed to within the logic
        # for establishing a similarity value proves more succinct.
        thumbnail = Thumbnail.from_image(keyframe.image)

        if is_color_image(keyframe.image):
            color_correlation = ColorCorrelation.from_image(keyframe.image)
        else:
            color_correlation = None

        orb = ORB.from_image(keyframe.image)
        if len(orb.descriptors) == 0:
            orb = None

        # TODO: set SSM, see previous TODO comment

        return FingerprintCollection(
            thumbnail, color_correlation, orb, video_name, segment_id
        )


def compare_thumbnails(
    query: FingerprintCollection,
    reference: FingerprintCollection,
    similarity_threshold=0.65,
) -> Tuple[bool, float]:
    S_th = query.thumbnail.similar_to(reference.thumbnail)
    return (S_th >= similarity_threshold, S_th)


def compare_color_correlation(
    query: FingerprintCollection,
    reference: FingerprintCollection,
    similarity_threshold=0.65,
) -> Tuple[bool, bool, float]:
    COULD_NOT_COMPARE = (False, False, 0)
    if query.color_correlation is None:
        # TODO: Include id
        logger.trace(
            'Could not compare CC because query image is in grayscale'
        )  # noqa: E501
        return COULD_NOT_COMPARE

    if reference.color_correlation is None:
        # TODO: Include id
        logger.trace(
            'Could not compare CC because reference image is in grayscale'
        )  # noqa: E501
        return COULD_NOT_COMPARE

    S_cc = query.color_correlation.similar_to(reference.color_correlation)

    return (True, S_cc >= similarity_threshold, S_cc)


def compare_orb(query, reference, similarity_threshold=0.7):
    COULD_NOT_COMPARE = (False, False, 0.0)

    query_has_descriptors = query.orb is not None
    reference_has_descriptors = reference.orb is not None
    can_compare = query_has_descriptors and reference_has_descriptors

    if not can_compare:
        s = (
            'Could not compare orb descriptors between'
            f' query={query.video_name}:{query.segment_id} and'
            f' reference={reference.video_name}:{reference.segment_id}'
            f' query_has_descriptors={query_has_descriptors}'
            f' reference_has_descriptors={reference_has_descriptors}'
        )
        logger.trace(s)
        return COULD_NOT_COMPARE

    S_orb = query.orb.similar_to(reference.orb)
    return (True, S_orb >= similarity_threshold, S_orb)


def compare_ssm(
    query: FingerprintCollection, reference: FingerprintCollection
) -> Tuple[bool, bool, float]:
    return False, False, 0


# TODO: re-implement using continuation style?
def __compare_fingerprints__(
    query: FingerprintCollection, reference: FingerprintCollection
) -> Tuple[MatchLevel, float]:

    similar_enough, S_th = compare_thumbnails(query, reference)

    if similar_enough:
        compare_cc = compare_color_correlation
        could_compare, similar_enough, S_cc = compare_cc(query, reference)

        if could_compare and similar_enough:
            could_compare, similar_enough, S_orb = compare_orb(
                query, reference
            )  # noqa: E501

            if could_compare and similar_enough:
                # Level A, visual fingerprints matched. Not processing audio
                w_th, w_cc, w_orb = 0.4, 0.3, 0.3
                similarity = w_th * S_th + w_cc * S_cc + w_orb * S_orb
                return (MatchLevel.LEVEL_A, similarity)
            else:
                could_compare, similar_enough, S_ssm = compare_ssm(
                    query, reference
                )  # noqa: E501
                if could_compare and similar_enough:
                    # Level B
                    w_th, w_cc, w_ssm = 0.4, 0.3, 0.2
                    similarity = w_th * S_th + w_cc * S_cc + w_ssm * S_ssm
                    return (MatchLevel.LEVEL_B, similarity)
                else:
                    w_th, w_cc = 0.5, 0.3
                    similarity = w_th * S_th + w_cc * S_cc
                    return (MatchLevel.LEVEL_C, similarity)
        else:
            could_compare, similar_enough, S_orb = compare_orb(
                query, reference
            )  # noqa: E501

            if could_compare and similar_enough:
                # Level D, video is in grayscale and local keypoints matched
                w_th, w_orb = 0.6, 0.4
                similarity = w_th * S_th + w_orb * S_orb
                return (MatchLevel.LEVEL_D, similarity)
            else:
                could_compare, similar_enough, S_ssm = compare_ssm(
                    query, reference
                )  # noqa: E501
                if could_compare and similar_enough:
                    w_th, w_ssm = 0.5, 0.2
                    similarity = w_th * S_th + w_ssm * S_ssm
                    return (MatchLevel.LEVEL_B, similarity)
                else:
                    w_th = 0.5  # TODO: What should the weight here be?
                    similarity = w_th * S_th
                    return (MatchLevel.LEVEL_F, similarity)
    else:
        # Thumbnails too dissimilar to continue comparing
        return (MatchLevel.LEVEL_G, 0)


@dataclass
class FingerprintComparison:
    query_video_name: str
    reference_video_name: str
    query_segment_id: int
    reference_segment_id: int
    match_level: MatchLevel
    similarity_score: float

    @staticmethod
    def compare(
        query_fpc: FingerprintCollection, reference_fpc: FingerprintCollection
    ) -> 'FingerprintComparison':
        match_level, similarity_score = __compare_fingerprints__(
            query_fpc, reference_fpc
        )

        return FingerprintComparison(
            query_fpc.video_name,
            reference_fpc.video_name,
            query_fpc.segment_id,
            reference_fpc.segment_id,
            match_level,
            similarity_score,
        )

    @staticmethod
    def compare_all(
        query_fps: List[FingerprintCollection],
        reference_fps: List[FingerprintCollection],
    ) -> Dict[int, List['FingerprintComparison']]:
        # Map from the segment id in the query video to a list of
        # tuples containing the reference segment id and the return
        # value of the fingerprint comparison
        all_comparisons = {
            query_fp.segment_id: [] for query_fp in query_fps
        }  # type: Dict[int, List[FingerprintComparison]]  # noqa: E501

        # sort by segment_id in the keys (0, 1, ...)
        all_comparisons = OrderedDict(sorted(all_comparisons.items()))

        for query_fpc in query_fps:
            for reference_fpc in reference_fps:
                logger.trace(
                    f'Comparing {query_fpc.video_name}:{query_fpc.segment_id} to {reference_fpc.video_name}:{reference_fpc.segment_id}'  # noqa: E501
                )

                comparison = FingerprintComparison.compare(query_fpc, reference_fpc)
                all_comparisons[query_fpc.segment_id].append(comparison)

        for segment_id, _ in all_comparisons.items():
            # Sort by the similarity score, making the highest similarity
            # items be listed first, i.e. 1.0 goes before 0.5
            comparison_similarity = (
                lambda comparison: comparison.similarity_score
            )  # noqa: E731, E501

            all_comparisons[segment_id] = sorted(
                all_comparisons[segment_id], key=comparison_similarity, reverse=True
            )

        return all_comparisons


# TODO: enable parallelism for long video files
def extract_fingerprint_collection(
    file_path: Path, root_output_directory: Path, segment_length_in_seconds=1
) -> List[FingerprintCollection]:
    segment_id_to_keyframe_fp_map = extract_fingerprint_collection_with_keyframes(
        file_path, root_output_directory, segment_length_in_seconds
    )

    # Extract the fingerprints, this is the fastest way as per
    # https://stackoverflow.com/a/13470505/5045375
    return list(dict(segment_id_to_keyframe_fp_map.values()).values())


def extract_fingerprint_collection_with_keyframes(
    file_path: Path, root_output_directory: Path, segment_length_in_seconds=1
) -> Dict[int, Tuple[Keyframe, FingerprintCollection]]:
    assert file_path.exists()

    # Note the use of .stem as opposed to .name, we do not want
    # the extension here,
    segments = segment(
        file_path,
        root_output_directory / file_path.stem,
        segment_length_in_seconds=segment_length_in_seconds,
    )
    downsamples = list(map(downsample, segments))

    fps = {}

    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions sometimes for videos with a fractional length
            # as the last segment might not contain any frames.
            continue

        keyframe = Keyframe.from_frame_paths(frame_paths)
        segment_id = util.segment_id_from_path(frame_paths[0])

        fpc = FingerprintCollection.from_keyframe(keyframe, file_path.name, segment_id)
        fps[segment_id] = (keyframe, fpc)

    return fps
