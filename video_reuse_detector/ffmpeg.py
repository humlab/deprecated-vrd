import subprocess

from loguru import logger
from pathlib import Path
from typing import List


def execute(cmd: str, output_directory: Path) -> List[Path]:
    if not output_directory.exists():
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
