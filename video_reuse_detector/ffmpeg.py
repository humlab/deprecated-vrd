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
    return f'[{str(output_paths[0])}, ..., {str(output_paths[-1])}]"'


def extract_outputs(log_file: str) -> List[Path]:
    output_paths: List[Path] = []

    with open(log_file, 'r') as log:
        output_paths = re.findall(".*Opening '(.*)' for writing", log.read())

    if len(output_paths) > 0:
        return list(map(Path, output_paths))

    with open(log_file, 'r') as log:
        output_paths = re.findall(".*Opening an output file: (.*)", log.read())

    return list(map(Path, output_paths))


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
        stderr=subprocess.DEVNULL, env=ffmpeg_env)

    output_paths = extract_outputs(log_file)

    os.remove(log_file)

    logger.debug(f'Produced output files: "{format_outputs(output_paths)}"')

    return output_paths
