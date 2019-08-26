from pathlib import Path
from typing import List
from loguru import logger

import shutil  # To remove directories
import cv2
import subprocess
import image_transformation

"""
This code implements the fingerprinting method proposed by Zobeida Jezabel
Guzman-Zavaleta in the thesis "An Effective and Efficient Fingerprinting Method
for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis,
specifically from the section 5.4 Discussion, where the author details the
parameter values that "proved" the "best" during her experiments.
"""


def execute_ffmpeg_command(ffmpeg_cmd: str, input_video: Path, output_directory: Path) -> List[Path]:
    logger.debug(f'Removing the directory "{output_directory}" if it exists and recreating it')
    shutil.rmtree(output_directory, ignore_errors=True)  # Might fail if permissions are off
    output_directory.mkdir(parents=True)

    logger.debug(f'Executing: "{ffmpeg_cmd}"')

    subprocess.call(ffmpeg_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    output_paths = list(output_directory.iterdir())

    logger.debug(f'Produced output files: "[{str(output_paths[0])}, ..., {str(output_paths[-1])}]"')

    return output_paths


def divide_into_segments(input_video: Path, output_directory: Path, segment_length_in_seconds=1) -> List[Path]:
    # -i                     input file
    # -codec:v libx264       re-encode so we can force keyframes
    # -force_key_frames      force keyframe every x seconds
    # -map 0                 use the given input file to produce all outputs
    # -f segment             output file will be multiple segments
    # -segment_time          length of each segment expressed in seconds
    ffmpeg_cmd = (
         'ffmpeg'
        f' -i {input_video}'
         ' -codec:v libx264'
        f' -force_key_frames expr:gte(t,n_forced*{segment_length_in_seconds})'
         ' -map 0'
         ' -f segment'
        f' -segment_time {segment_length_in_seconds}'
        f' {output_directory}/{input_video.stem}-segment%03d.mp4'
         )

    return execute_ffmpeg_command(ffmpeg_cmd, input_video, output_directory)


def downsample_video(input_video: Path, output_directory: Path, fps=5) -> List[Path]:
    """
    Assumes that the given path refers to a video file and extracts an `fps`
    number of frames from every second of the specified video.

    For instance, for a video "video.mp4" `downsample_video(Path('video.mp4'),
    fps=5)` will yield 5 frames for every second of said video. If said video
    is, for instance, 10 seconds long, the number of frames that are produced
    is equal to 50.

    The return value is a list of all these frames.
    """
    ffmpeg_cmd = (
        'ffmpeg'
       f' -i {input_video}'
       f' -vf fps={fps}'
       f' {output_directory}/{input_video.stem}-frame%03d.png'
    )

    return execute_ffmpeg_command(ffmpeg_cmd, input_video, output_directory)


def crop_with_central_alignment(image, m=320, n=320):
    """
    Crops the given image to a (M x N) area with central alignment
    """
    height, width, _ = image.shape
    center_y, center_x = height/2, width/2
    starting_row, starting_column = int(center_y - m/2), int(center_x - n/2)

    img = image[starting_row:starting_row + m, starting_column:starting_column + n]

    return img


def average_frames(frames):
    """
    Average the given set of frames equally across all pixel values and channels
    as per Eq. 4.1.
    """
    return image_transformation.average(frames)


def keyframe(frames):
    kf = average_frames(frames)
    kf = image_transformation.scale(kf, scale_factor=1.2)
    return crop_with_central_alignment(kf)


def imread(filename: Path):
    return cv2.imread(str(filename))


def imwrite(filename: Path, image):
    filename.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(filename), image)


def produce_fingerprints(input_video: Path, output_directory: Path):
    # TODO: Produce audio fingerprints, this just creates keyframes
    # TODO: Clean-up intermediary directories
    segments = divide_into_segments(input_video, output_directory / 'segments')

    segment_id = 0
    for segment in segments:
        frame_paths = downsample_video(segment, output_directory / 'frames' / f'segment{segment_id:03}')

        kf = keyframe([imread(filename) for filename in frame_paths])

        imwrite(output_directory / 'keyframes' / f'{input_video.stem}-keyframe{segment_id:03}.png', kf)
        imwrite(output_directory / 'thumbs' / f'{input_video.stem}-thumb{segment_id:03}.png', produce_thumbnail(kf))
        segment_id += 1


def fold(image):
    """
    TODO: Figure out the correct way to do this.

    The paper (p.64) says to split an image into its left and right
    constituents, like so

    def left(image):
        _, width, _ = image.shape
        return image[:, 0:int(width/2)]  # 1.5 => 1 when cast to int


    def right(image):
        _, width, _ = image.shape
        return image[:, int(width/2) + 1::]


    image_l, image_r = left(image), right(image)

    And then overlay the pair equally, after first having flipped the right
    half on the horizontal axis, i.e.

    return cv2.addWeighted(image_l, 0.5, cv2.flip(image_r, 1), 0.5, gamma=0.0)

    and that the produced image should be invariant against horizontal
    flipping attacks but experimentally the return value below is what has been
    found to be invariant against such attacks,
    """
    return cv2.addWeighted(image, 0.5, cv2.flip(image, 1), 0.5, 0)


def equalize_histogram(image):
    return cv2.equalizeHist(image_transformation.grayscale(image))


def produce_normalized_grayscale_image(image, strategy=equalize_histogram):
    """
    TODO: Page 64 of the paper describes a difference approach for normalizing
    the grayscale image that is something akin to,

    grayscale_image = grayscale(image).astype(numpy.float32) / 255

    and then,

    normalized_image = (grayscale_image - grayscale_image.mean()) / grayscale_image.std()

    or equivalently,

    grayscale_image -= grayscale_image.mean()
    grayscale_image /= grayscale_image.std()
    normalized_image = grayscale_image

    And finally,
    return normalized_image * 255

    but applied on a block-by-block basis. Let this serve as a place-holder
    for now and re-visit this portion of the code later.
    """
    return strategy(image)


def produce_thumbnail(image, m=30):
    folded_grayscale = fold(produce_normalized_grayscale_image(image))

    # Assume that converting the image to a m x m image is effectively
    # downsizing the image, hence interpolation=cv2.INTER_AREA
    return cv2.resize(folded_grayscale, (m, m), interpolation=cv2.INTER_AREA)