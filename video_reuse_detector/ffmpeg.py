import subprocess

from loguru import logger
from pathlib import Path
from typing import List

import re
import random
import os


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
