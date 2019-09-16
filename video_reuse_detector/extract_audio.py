from loguru import logger
from typing import List
from pathlib import Path

from video_reuse_detector import ffmpeg


def extract(
    input_video: Path,
    output_directory: Path,
        segment_length_in_seconds=1) -> List[Path]:
    # TODO: Verify that input video has an audiostream
    # TODO: Determine audiostream codec
    #
    # -i                     input file
    # -vn                    the video stream is not processed and is not
    #                        used in the output file.
    # -acodec copy           copy, do not process, audio stream. Faster.
    ffmpeg_cmd = (
         'ffmpeg'
         f' -i {input_video}'
         ' -vn'
         ' -acodec copy'
         f' {output_directory}/{input_video.stem}.aac'
         )

    segment_paths = ffmpeg.execute(ffmpeg_cmd, output_directory)

    print(*segment_paths, sep='\n')

    return segment_paths


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Extract audio from input file')

    parser.add_argument(
        'input_videos',
        nargs='+',
        default=sys.stdin,
        help='The videos to extract audio from')

    args = parser.parse_args()
    for video_path in args.input_videos:
        dst = Path(video_path).parent
        logger.debug(f'Downsampling {video_path}, output to {dst}')
        extract(Path(video_path), dst)
