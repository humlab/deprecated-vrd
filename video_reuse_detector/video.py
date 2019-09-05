import shutil  # To remove directories
import subprocess

from loguru import logger
from pathlib import Path
from typing import List, Dict


def execute_ffmpeg_command(cmd: str, output_directory: Path) -> List[Path]:
    logger.debug(f'Removing the directory "{output_directory}" if it exists')

    # Might fail if permissions are off
    # TODO: Let the caller worry about this instead, maybe we don't want to do
    # any work if the directory already exists? Overwrite flag?
    shutil.rmtree(output_directory, ignore_errors=True)
    logger.debug(f'Creating "{output_directory}" and parents if necessary')
    output_directory.mkdir(parents=True)

    logger.debug(f'Executing: "{cmd}"')

    subprocess.call(
        cmd.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    output_paths = list(output_directory.iterdir())

    # Sort to make the log output coherent
    output_paths.sort()
    outputs_pretty = f'[{str(output_paths[0])}, ..., {str(output_paths[-1])}]"'

    logger.debug(f'Produced output files: "{outputs_pretty}"')

    return output_paths


def segment_id_from_path(path):
    stem = path.stem
    # Find the index within the stem at which the word "segment" begins
    segment_suffix_idx = stem.rfind('segment')

    # Remove the word "segment",
    segment_id = stem[segment_suffix_idx:].replace('segment', '')

    return int(segment_id)


def segment(
    input_video: Path,
    output_directory: Path,
        segment_length_in_seconds=1) -> Dict[int, Path]:
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

    segment_paths = execute_ffmpeg_command(ffmpeg_cmd, output_directory)
    id_to_path_map = {segment_id_from_path(p): p for p in segment_paths}

    return id_to_path_map


def downsample(input_video: Path, output_directory: Path, fps=5) -> List[Path]:
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

    return execute_ffmpeg_command(ffmpeg_cmd, output_directory)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Video segmentation and downsampling')

    supported_operations = {
        'downsample': downsample,
        'segment': segment
    }

    parser.add_argument(
        'operation',
        choices=supported_operations.keys(),
        help='The operation to execute')

    parser.add_argument(
        'input_video',
        help='The video to apply the given operation to')

    parser.add_argument(
        'output_directory',
        help='A directory to write the outputs to')

    args = parser.parse_args()
    operation = supported_operations[args.operation]
    operation(Path(args.input_video), Path(args.output_directory))
