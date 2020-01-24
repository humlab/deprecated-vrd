from pathlib import Path
from typing import List

from loguru import logger

from video_reuse_detector import ffmpeg


def downsample(input_video: Path, output_directory: Path = None, fps=5) -> List[Path]:
    """
    Assumes that the given path refers to a video file and extracts an `fps`
    number of frames from every second of the specified video.

    For instance, for a video "video.mp4" `downsample_video(Path('video.mp4'),
    fps=5)` will yield 5 frames for every second of said video. If said video
    is, for instance, 10 seconds long, the number of frames that are produced
    is equal to 50.

    The return value is a list of all these frames.
    """
    if output_directory is None:
        output_directory = input_video.parent

    # TODO: Always yield strictly fps number of frames.
    ffmpeg_cmd = (
        'ffmpeg'
        f' -i {input_video}'
        f' -vf fps={fps}'
        f' {output_directory}/frame%03d.png'
    )

    logger.debug(f'Downsampling "{input_video}"')
    frame_paths = ffmpeg.execute(ffmpeg_cmd, output_directory)
    logger.debug(f'Downsampling produced output="{list(map(str, frame_paths))}"')

    return frame_paths


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Video downsampling')

    parser.add_argument(
        'input_videos', nargs='+', default=sys.stdin, help='The videos to downsample'
    )

    args = parser.parse_args()

    for video_path in args.input_videos:
        outputs = downsample(Path(video_path))

        print(*outputs, sep='\n')
