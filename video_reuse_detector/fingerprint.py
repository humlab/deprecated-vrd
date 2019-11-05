from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

import numpy as np
from loguru import logger

from video_reuse_detector.color_correlation import ColorCorrelation
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.orb import ORB
from video_reuse_detector.thumbnail import Thumbnail


class MatchLevel(Enum):
    LEVEL_A = auto()
    LEVEL_B = auto()
    LEVEL_C = auto()
    LEVEL_D = auto()
    LEVEL_F = auto()
    LEVEL_G = auto()


@dataclass
class FingerprintComparison:
    query_video_name: str
    reference_video_name: str
    query_segment_id: int
    reference_segment_id: int
    level: MatchLevel
    similarity: float


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
        )  # noqa: E501


def compare_thumbnails(
    query: FingerprintCollection,
    reference: FingerprintCollection,
    similarity_threshold=0.65,
) -> Tuple[bool, float]:
    S_th = query.thumbnail.similar_to(reference.thumbnail)
    return (S_th >= similarity_threshold, S_th)


# Could be compared, threshold exceeded, similarity score
def compare_color_correlation(
    query: FingerprintCollection,
    reference: FingerprintCollection,
    similarity_threshold=0.65,
) -> Tuple[bool, bool, float]:
    COULD_NOT_COMPARE = (False, False, 0)
    if query.color_correlation is None:
        # TODO: Include id
        logger.debug(
            'Could not compare CC because query image is in grayscale'
        )  # noqa: E501
        return COULD_NOT_COMPARE

    if reference.color_correlation is None:
        # TODO: Include id
        logger.debug(
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
        logger.debug(s)
        return COULD_NOT_COMPARE

    S_orb = query.orb.similar_to(reference.orb)
    return (True, S_orb >= similarity_threshold, S_orb)


def compare_ssm(
    query: FingerprintCollection, reference: FingerprintCollection
) -> Tuple[bool, bool, float]:
    return False, False, 0


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


def compare_fingerprints(
    query: FingerprintCollection, reference: FingerprintCollection
) -> FingerprintComparison:
    comparison = __compare_fingerprints__(query, reference)

    return FingerprintComparison(
        query.video_name,
        reference.video_name,
        query.segment_id,
        reference.segment_id,
        comparison[0],
        comparison[1],
    )
