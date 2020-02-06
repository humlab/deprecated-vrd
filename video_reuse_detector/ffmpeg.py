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


def execute(cmd: str, output_directory: Path) -> List[Path]:
    if not output_directory.exists():
        logger.debug(f'Creating "{output_directory}" and parents if necessary')
        output_directory.mkdir(parents=True)

    logger.debug(f'Executing: "{cmd}"')

    # TODO: Use tempfile?
    log_file = f'ffreport{random.randint(0, 1000)}.log'
    ffmpeg_env = {'FFREPORT': f'file={log_file}:level=48'}

    subprocess.call(
        cmd.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=ffmpeg_env,
    )

    try:
        output_paths = extract_outputs(log_file)
        os.remove(log_file)
    except FileNotFoundError:
        msg = (
            f'Could not read/remove log file "{log_file}"'
            f'as it does not exist while executing "{cmd}"'
        )
        logger.warning(f'${msg}. log_file="{log_file}"')

    logger.info(f'Produced output files: "{format_outputs(output_paths)}"')

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
    suffix = f"{ss.replace(':', '')}_{duration.replace(':', '')}"

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
    # we get "ATW-550_000030_000005.mpg"
    extension = file_path.suffix  # includes the ".", so for instance ".mpg"
    name_of_new_file = f'{file_path.stem}_{suffix}{extension}'
    output_path = output_directory / Path(name_of_new_file)

    # If overwrite=False, and the file already exists, echo it back as we do
    # not want to recreate it!
    if not overwrite and output_path.exists():
        logger.debug(f'{output_path} exists already, returning without calling ffmpeg')
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
