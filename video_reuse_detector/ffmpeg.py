import os
import random
import re
import subprocess
from pathlib import Path
from typing import List

from loguru import logger


def format_outputs(output_paths: List[Path]) -> str:
    if len(output_paths) == 0:
        return "[]"

    # Sort to make the log output coherent
    output_paths.sort()

    if len(output_paths) == 1:
        return f'[{output_paths[0]}]'

    return f'[{str(output_paths[0])}, ..., {str(output_paths[-1])}]"'


def extract_outputs(log_file: str) -> List[Path]:
    output_paths: List[Path] = []

    with open(log_file, 'r') as log:
        output_paths = re.findall(".*Opening '(.*)' for writing", log.read())

    if len(output_paths) > 0:
        return list(map(Path, output_paths))

    with open(log_file, 'r') as log:
        regex = '.*Opening an output file: (.*).'
        output_paths = re.findall(regex, log.read())

    all_paths = list(map(Path, output_paths))

    return list(filter(lambda path: path.exists(), all_paths))


def execute(cmd: str, output_directory: Path, remove_log=True) -> List[Path]:
    if not output_directory.exists():
        msg = (
            f'Output directory "{output_directory}" does not exist.'
            ' Creating it (and parents - if necessary)'
        )
        logger.debug(msg)
        output_directory.mkdir(parents=True)
    else:
        logger.trace(f'Output directory "{output_directory}" exists already')

    # TODO: Use tempfile?
    log_file = f'ffreport{random.randint(0, 1000)}.log'
    ffmpeg_env = {'FFREPORT': f'file={log_file}:level=48'}

    if not os.access(str(output_directory), os.X_OK | os.W_OK):
        logger.error(f'Do not have write access to {output_directory}')
        raise PermissionError

    logger.debug(f'Executing: "{cmd}", logging to "{log_file}"')

    subprocess.call(
        cmd.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=ffmpeg_env,
    )

    try:
        output_paths = extract_outputs(log_file)

        if remove_log:  # Usually True, but handy for debugging
            os.remove(log_file)
    except FileNotFoundError:
        msg = (
            f'Could not read/remove log file "{log_file}"'
            f'as it does not exist while executing "{cmd}"'
        )
        logger.warning(f'${msg}. log_file="{log_file}"')

    if output_paths == []:
        logger.warning(f'Executing \"{cmd}\" did not produce any output!')
    else:
        logger.trace(f'Produced output files: "{format_outputs(output_paths)}"')

    return output_paths


def get_video_duration(file_path: Path) -> float:
    # Duration of container
    ffprobe_cmd = (
        'ffprobe'
        ' -v error'
        ' -show_entries'
        ' format=duration'
        ' -of default=noprint_wrappers=1:nokey=1'
        f' {str(file_path)}'
    )

    return float(subprocess.check_output(ffprobe_cmd.split()))


def slice(
    file_path: Path, ss: str, duration: str, output_directory: Path, overwrite=False
) -> Path:
    # Incoming strings on the form HH:MM:SS turned into HHMMSS
    suffix = f"start_{ss.replace(':', '')}_duration_{duration.replace(':', '')}"

    # Concatenate into the original file name, append a delimiting underscore
    # add the extension of the original file, so for,
    #
    # file_path=/some/path/to/ATW-550.mpg
    #
    # and,
    #
    # ss='00:00:30'
    # duration='00:00:05'
    #
    # we get "ATW-550_start_000030_duration_000005.mpg"
    extension = file_path.suffix  # includes the ".", so for instance ".mpg"
    name_of_new_file = f'{file_path.stem}_{suffix}{extension}'
    output_path = output_directory / Path(name_of_new_file)

    # If overwrite=False, and the file already exists, echo it back as we do
    # not want to recreate it!
    if not overwrite and output_path.exists():
        logger.warning(
            f'{output_path} exists already, returning without calling ffmpeg'
        )
        return output_path

    cmd = (
        'ffmpeg'
        f' -ss {ss}'
        f' -i {str(file_path)}'
        f' -to {duration}'
        ' -c copy'
        f' -y {str(output_path)}'
    )

    return execute(cmd, output_path.parent)[0]


def __method__():
    import traceback

    return traceback.extract_stack(None, 2)[0][2]


def get_output_file_name(input_file: Path, video_filter: str, params={}) -> Path:
    extension = input_file.suffix  # includes the ".", so for instance ".mp4"

    name_of_new_file = f'{input_file.stem}_{video_filter}'

    if params != {}:
        # Join all k, v pairs with an underscore between them
        suffix = '_'.join(f'{k}_{v}' for k, v in params.items())
        name_of_new_file = f'{name_of_new_file}_{suffix}'

    name_of_new_file += extension

    return Path(name_of_new_file)


# blur (gaussian, motion),
#
# See: https://medium.com/@allanlei/blur-out-videos-with-ffmpeg-92d3dc62d069
def blur(
    input_file: Path,
    output_directory: Path,
    luma_radius=2,
    chroma_radius=10,
    luma_power=1,
) -> Path:
    params = {
        'luma_radius': luma_radius,
        'chroma_radius': chroma_radius,
        'luma_power': luma_power,
    }

    output_file_name = get_output_file_name(input_file, __method__(), params)
    output_path = output_directory / output_file_name
    logger.debug(
        f'Applying {__method__()} with params={params} on {input_file} producing {output_path}'  # noqa: E501
    )

    cmd = (
        f'ffmpeg -i {input_file}'
        ' -filter_complex '
        f'[0:v]boxblur=luma_radius={luma_radius}'
        f':chroma_radius={chroma_radius}'
        f':luma_power={luma_power}[blurred]'
        ' -map [blurred]'
        f' {output_path}'
    )

    return execute(cmd, output_path.parent)[0]


def get_frame_at_time(input_file: Path, output_directory: Path, timestamp: str) -> Path:
    output_file_name = f"{input_file.stem}_{timestamp.replace(':', '')}.png"
    output_path = output_directory / output_file_name
    logger.debug(f'Applying {__method__()} on {input_file} producing {output_path}')

    cmd = f'ffmpeg -ss {timestamp} -i {input_file} -vframes 1 {output_path}'

    return execute(cmd, output_path.parent)[0]


def apply_frei0r_filter(
    input_file: Path, output_directory: Path, video_filter: str, overwrite=False
) -> Path:
    assert input_file.exists()

    output_file_name = get_output_file_name(input_file, video_filter)
    output_path = output_directory / output_file_name

    if not overwrite and output_path.exists():
        logger.warning(
            f'{output_path} exists already, returning without calling ffmpeg'
        )
        return output_path

    logger.debug(f"Adding {video_filter} to {input_file} producing {output_path}")

    return execute(
        f'ffmpeg -i {input_file} -vf frei0r={video_filter}'
        f' -c:a copy -pix_fmt yuv420p {output_path}',
        output_path.parent,
    )[0]


def softglow(input_file: Path, output_directory: Path, overwrite=False) -> Path:
    return apply_frei0r_filter(input_file, output_directory, __method__(), overwrite)


def hflip(input_file: Path, output_directory: Path, overwrite=False) -> Path:
    output_file_name = get_output_file_name(input_file, __method__())
    output_path = output_directory / output_file_name

    if not overwrite and output_path.exists():
        logger.warning(
            f'{output_path} exists already, returning without calling ffmpeg'
        )
        return output_path

    logger.debug(f"Adding {__method__()} to {input_file} producing {output_path}")

    return execute(
        f'ffmpeg -i {input_file} -vf hflip -c:a copy {output_path}', output_path.parent,
    )[0]


def get_video_dimensions(file_path: Path) -> str:
    # Duration of container
    ffprobe_cmd = (
        'ffprobe'
        ' -v error'
        ' -show_entries'
        ' stream=width,height'
        ' -of csv=p=0:s=x'
        f' {str(file_path)}'
    )

    return subprocess.check_output(ffprobe_cmd.split()).decode().rstrip()


def tint(
    input_file: Path, output_directory: Path, color='red', overwrite=False
) -> Path:
    # The color has the [0x|#]RRGGBB[AA] format.
    # https://ffmpeg.org/ffmpeg-utils.html#Color
    output_file_name = get_output_file_name(input_file, __method__())
    output_path = output_directory / output_file_name

    if not overwrite and output_path.exists():
        logger.warning(
            f'{output_path} exists already, returning without calling ffmpeg'
        )
        return output_path

    logger.debug(f"Adding {__method__()} to {input_file} producing {output_path}")
    dimensions = get_video_dimensions(input_file)
    logger.debug(f'Input file has dimensions {dimensions}')

    return execute(
        f'ffmpeg -i {input_file} -f lavfi -i color={color}:s={dimensions}'
        ' -filter_complex [0:v]setsar=sar=1/1[s];[s][1:v]blend=shortest=1:all_mode=overlay:all_opacity=0.7[out]'  # noqa: E501
        f' -map [out] -map 0:a {output_path}',
        output_path.parent,
    )[0]


def filters():
    return {
        'blur': lambda input_file, output_directory: blur(input_file, output_directory),
        'hflip': hflip,
        'softglow': softglow,
        'tint': tint,
    }


def video_stats(video_file: Path):
    """
    Return all available stats for the given video file
    """

    return {
        video_file.name: {
            'duration': get_video_duration(video_file),
            'dimensions': get_video_dimensions(video_file),
        }
    }
