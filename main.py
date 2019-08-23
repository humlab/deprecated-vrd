from pathlib import Path
from typing import List
from loguru import logger

import shutil  # To remove directories
import cv2
import subprocess

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


def scale_image(image, scale_factor):
    height, width, _ = image.shape

    # Another option for upscaling is INTER_CUBIC which is slower but
    # produces a better looking output. Using INTER_LINEAR for now
    interpolation_method = cv2.INTER_LINEAR if scale_factor >= 1 else cv2.INTER_AREA
    return cv2.resize(image, (int(width*scale_factor), int(height*scale_factor)), interpolation=interpolation_method)


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
    import numpy

    # Assume all frames are of the same dimensions
    height, width, channels = frames[0].shape

    frame_average = numpy.zeros((height, width, channels), numpy.float)

    for frame in frames:
        frame_average = frame_average + frame/len(frames)

    frame_average = numpy.array(numpy.round(frame_average), dtype=numpy.uint8)
    return frame_average


def imread(filename: Path):
    return cv2.imread(str(filename))


def imwrite(filename: Path, image):
    filename.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(filename), image)


def produce_fingerprints(input_video: Path):
    # TODO: Produce audio fingerprints, this just creates keyframes
    # TODO: Clean-up intermediary directories

    output_directory = Path(f'fingerprints/{input_video.stem}')

    segments = divide_into_segments(input_video, output_directory / 'segments')

    segment_id = 0
    for segment in segments:
        frame_paths = downsample_video(segment, output_directory / 'frames' / f'segment{segment_id:03}')

        keyframe = average_frames([imread(filename) for filename in frame_paths])
        keyframe = scale_image(keyframe, scale_factor=1.2)
        keyframe = crop_with_central_alignment(keyframe)

        imwrite(output_directory / 'keyframes' / f'{input_video.stem}-keyframe{segment_id:03}.png', keyframe)
        segment_id += 1


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def left(image):
    _, width, _ = image.shape
    return image[:, 0:int(width/2)]  # 1.5 => 1 when cast to int


def right(image):
    _, width, _ = image.shape
    return image[:, int(width/2) + 1::]


def fold(image):
    """
    TODO: Figure out the correct way to do this.

    The paper (p.64) says to split an image into its left and right
    constituents, like so

    image_l, image_r = left(image), right(image)

    And then overlay the pair equally, after first having flipped the right
    half on the horizontal axis, i.e.

    return cv2.addWeighted(image_l, 0.5, cv2.flip(image_r, 1), 0.5, gamma=0.0)

    and that the produced image should be invariant against horizontal
    flipping attacks but experimentally the return value below is what has been
    found to be invariant against such attacks,
    """
    return cv2.addWeighted(image, 0.5, cv2.flip(image, 1), 0.5, 0)
