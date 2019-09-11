import numpy as np
import cv2

from typing import List, Dict, Tuple
from dataclasses import dataclass

from pathlib import Path
from loguru import logger

from video_reuse_detector import util, image_transformation, video


"""
This code implements the fingerprinting method proposed by Zobeida Jezabel
Guzman-Zavaleta in the thesis "An Effective and Efficient Fingerprinting Method
for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis,
specifically from the section 5.4 Discussion, where the author details the
parameter values that "proved" the "best" during her experiments.
"""


def crop_with_central_alignment(image, m=320, n=320):
    """
    Crops the given image to a (M x N) area with central alignment
    """
    height, width, _ = image.shape
    center_y, center_x = height/2, width/2
    starting_row, starting_column = int(center_y - m/2), int(center_x - n/2)

    img = image[starting_row:starting_row + m,
                starting_column:starting_column + n]

    return img


def average_frames(frames):
    """
    Average the given set of frames equally across all pixel values and
    channels as per Eq. 4.1.
    """
    return image_transformation.average(frames)


def fold(image):
    """
    Takes a given image and folds it so that the resulting output image is
    invariant against horizontal attacks,

    While the input is semantically an image, it will accept any numpy array.
    We will use the words image, array, and matrix, interchangably when
    referring to the input and output here.

    So, for

    >>> import numpy as np
    >>> image = np.arange(6).reshape(3, 2)
    >>> folded_image = fold(image)

    the output will satisfy the following conditions,

    Condition 1. The shape of the input "image" is retained,

    >>> folded_image.shape == image.shape
    True

    Condition 2. The output matrix, when flipped horizontally, will remain
    unchanged,

    >>> flip_horizontal = lambda image: cv2.flip(image, 1)
    >>> np.array_equal(folded_image, flip_horizontal(folded_image))
    True
    """
    return cv2.addWeighted(image, 0.5, cv2.flip(image, 1), 0.5, 0)


def map_over_blocks(image, f, nr_of_blocks=16):
    block_img = np.zeros(image.shape)
    im_h, im_w = image.shape[:2]
    bl_h, bl_w = util.compute_block_size(image, nr_of_blocks)

    for row in np.arange(im_h - bl_h + 1, step=bl_h):
        for col in np.arange(im_w - bl_w + 1, step=bl_w):
            block_to_process = image[row:row+bl_h, col:col+bl_w]
            block_img[row:row+bl_h, col:col+bl_w] = f(block_to_process)

    return block_img


def produce_normalized_grayscale_image(image):
    def zscore(block):
        mean = np.mean(block)
        std = np.std(block)
        return mean - std

    return map_over_blocks(image_transformation.grayscale(image), zscore)


def produce_thumbnail(image, m=30):
    folded_grayscale = fold(produce_normalized_grayscale_image(image))

    # Assume that converting the image to a m x m image is effectively
    # downsizing the image, hence interpolation=cv2.INTER_AREA
    return cv2.resize(folded_grayscale, (m, m), interpolation=cv2.INTER_AREA)


def extract_video_source(keyframe_file: Path) -> str:
    """Extracts video source from a path to a keyframe

    A valid keyframe filename is assumed to be on the form,

    {video-source}-segment{segment_id}-keyframe{keyframe_id}.png

    >>> extract_video_source(Path('dive-segment001-keyframe000.png'))
    'dive'
    """
    stem = keyframe_file.stem

    return stem[:stem.find('-')]


def extract_segment_id(keyframe_file: Path) -> str:
    """
    >>> extract_segment_id(Path('dive-segment001-keyframe000.png'))
    '001'
    """
    stem = keyframe_file.stem
    idx = stem.find('segment') + len('segment')

    return stem[idx:idx+3]


@dataclass
class FingerprintMetadata:
    video_source: Path
    segment_id: int


@dataclass
class Keyframe:
    image: np.ndarray
    metadata: FingerprintMetadata

    @staticmethod
    def from_frames(video_source: Path,
                    segment_id: int,
                    frames: List[np.ndarray]) -> 'Keyframe':
        kf = average_frames(frames)
        kf = image_transformation.scale(kf, scale_factor=1.2)
        kf = crop_with_central_alignment(kf)

        metadata = FingerprintMetadata(video_source, segment_id)

        return Keyframe(kf, metadata)

    @staticmethod
    def from_file(keyframe_file: Path) -> 'Keyframe':
        video_source = extract_video_source(keyframe_file)
        segment_id = int(extract_segment_id(keyframe_file))
        metadata = FingerprintMetadata(video_source, segment_id)

        return Keyframe(imread(keyframe_file), metadata)


@dataclass
class Thumbnail:
    image: np.ndarray
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'Thumbnail':
        thumb = produce_thumbnail(keyframe.image)
        return Thumbnail(thumb, keyframe, keyframe.metadata)


@dataclass
class ORB:
    descriptors: List[List[int]]
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'ORB':
        # TODO: Use folded variant, but OpenCV freaks out
        f_grayscale = image_transformation.grayscale(keyframe.image)

        # Note we use ORB_create() instead of ORB() as the latter invocation
        # results in a TypeError, specifically,
        #
        # TypeError: Incorrect type of self (must be 'Feature2D' or its
        # derivative)
        #
        # because of a compatability issue (wrapper related), see
        # https://stackoverflow.com/a/49971485
        #
        # We set nfeatures=250 as per p. 103 in the paper.
        orb = cv2.ORB_create(nfeatures=250, scoreType=cv2.ORB_FAST_SCORE)

        # find the keypoints with ORB
        kps, des = orb.detectAndCompute(f_grayscale, None)

        if des is None:
            des = []  # No features found

        return ORB(des, keyframe, keyframe.metadata)


@dataclass
class ColorCorrelation:
    histogram: Dict[str, float]
    as_number: int
    created_from: Keyframe
    metadata: FingerprintMetadata

    @staticmethod
    def from_keyframe(keyframe: Keyframe) -> 'ColorCorrelation':
        from video_reuse_detector import color_correlation

        cc_hist = color_correlation.color_correlation_histogram(keyframe.image)
        encoded = color_correlation.feature_representation(cc_hist)
        return ColorCorrelation(cc_hist, encoded, keyframe, keyframe.metadata)


@dataclass
class FingerprintCollection:
    th: Thumbnail
    cc: ColorCorrelation
    orb: ORB
    metadata: FingerprintMetadata

    def __init__(self, keyframe, saliency_map=None):
        self.th = Thumbnail.from_keyframe(keyframe)
        self.cc = ColorCorrelation.from_keyframe(keyframe)
        self.orb = ORB.from_keyframe(keyframe)
        fps = [self.th, self.cc, self.orb]

        assert(all(fp.metadata == keyframe.metadata for fp in fps))
        self.metadata = keyframe.metadata


def imread(filename: Path):
    return cv2.imread(str(filename))


def imwrite(filename: Path, image):
    filename.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(filename), image)


def extract_frames(segment_id: int,
                   segment: Path,
                   output_directory: Path) -> Tuple[List[np.ndarray],
                                                    List[Path]]:
    frames_dir = output_directory / 'frames'
    frames_output_directory = frames_dir / f'segment{segment_id:03}'
    frame_paths = video.downsample(segment, frames_output_directory)
    frames = [imread(filename) for filename in frame_paths]

    return (frames, frame_paths)


def extract_fingerprints_from_segment(segment_id: int,
                                      segment: Path,
                                      output_directory: Path) -> Tuple[
                                          Keyframe,
                                          FingerprintCollection]:

    frames, _ = extract_frames(segment_id, segment, output_directory)
    kf = Keyframe.from_frames(segment, segment_id, frames)

    return (kf, FingerprintCollection(kf))


def store_keyframe(kf: Keyframe, output_directory: Path):
    # TODO: Move to Keyframe class?
    # Add indirection to support DB- and filesystem-writes
    kf_dir = output_directory / 'keyframes'
    input_video = kf.metadata.video_source
    segment_id = kf.metadata.segment_id

    dst = kf_dir / f'{input_video.stem}-keyframe{segment_id:03}.png'

    imwrite(dst, kf.image)


def store_thumbnail(th: Thumbnail, output_directory: Path):
    thumbs_dir = output_directory / 'thumbs'
    input_video = th.metadata.video_source
    segment_id = th.metadata.segment_id

    dst = thumbs_dir / f'{input_video.stem}-thumb{segment_id:03}.png'

    imwrite(dst, th.image)


def produce_fingerprints(
    input_video: Path,
    output_directory: Path) -> Dict[int,
                                    FingerprintCollection]:
    # TODO: Produce audio fingerprints, this just creates keyframes
    # TODO: Clean-up intermediary directories
    # TODO: Perform as a sequence of operations instead,
    #
    #       1. segment using "python video segment <file> <output_dir>"
    #       2. downsample using "python video downsample <output_dir/**>"
    #       3. create fingerprints from the frames from 2.
    segments = video.segment(input_video, output_directory / 'segments')

    # TODO: Map superfluous? FingerprintCollection contains id
    id_to_fingerprint_map = {}

    for segment_id, segment in segments.items():
        logger.debug(f'Processing segment_id={segment_id}')
        kf, fingerprints = extract_fingerprints_from_segment(segment_id,
                                                             segment,
                                                             output_directory)

        store_keyframe(kf, output_directory)
        store_thumbnail(fingerprints.th, output_directory)

        metadata = fingerprints.metadata
        # TODO: Restore: assert(metadata.video_source == input_video)
        assert(metadata.segment_id == segment_id)

        if len(fingerprints.orb.descriptors) == 0:
            logger.warning(f'No features found for keyframe: {metadata}')

        id_to_fingerprint_map[segment_id] = fingerprints

    return id_to_fingerprint_map


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    import argparse

    parser = argparse.ArgumentParser(
        description='Fingerprint extractor for video files')

    parser.add_argument(
        'input_video',
        help='The video to extract fingerprints from')

    parser.add_argument(
        'output_directory',
        help='A directory to write the created fingerprints and artefacts to')

    args = parser.parse_args()
    input_video = Path(args.input_video)
    produce_fingerprints(input_video, Path(args.output_directory))
