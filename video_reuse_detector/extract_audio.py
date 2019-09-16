
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

    parser = argparse.ArgumentParser(
        description='Extract audio from input file')

    parser.add_argument(
        'output_directory',
        help='A directory to write the outputs to')

    parser.add_argument(
        'input_video',
        help='The video to extract audio from')

    args = parser.parse_args()
    extract(Path(args.input_video), Path(args.output_directory))
