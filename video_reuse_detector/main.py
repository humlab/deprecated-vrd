from loguru import logger
from pathlib import Path
from typing import List


def list_keyframe_paths(directory: Path, glob_pattern: str) -> List[Path]:
    return list(directory.glob(glob_pattern))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Video reuse detector')

    parser.add_argument(
        'query_fingerprints_directory',
        help='A directory with fingerprints')

    parser.add_argument(
        'reference_fingerprints_directory',
        help='A directory with subdirectories where each contains fingerprints for a video')  # noqa: E501

    args = parser.parse_args()

    query_directory = Path(args.query_fingerprints_directory)
    logger.debug(f'Treating "{query_directory}" as the query "video"')

    glob_pattern = '**/keyframe.png'
    query_keyframe_paths = list_keyframe_paths(query_directory, glob_pattern)
    logger.debug(f'Found {len(query_keyframe_paths)} keyframes under "{query_directory}" (glob_pattern="{glob_pattern}")')  # noqa: E501
