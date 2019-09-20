from loguru import logger
from pathlib import Path
from typing import Dict, List


def list_keyframe_paths(directory: Path, glob_pattern: str) -> List[Path]:
    return list(directory.glob(glob_pattern))


def list_reference_keyframes(directory: Path,
                             glob_pattern: str) -> Dict[str, List[Path]]:
    video_to_keyframe_paths_map = {}

    if not directory.is_dir():
        raise ValueError(f'Expected "directory={directory} to be a directory')

    for d in directory.iterdir():
        video_to_keyframe_paths_map[d] = list_keyframe_paths(d, glob_pattern)

    return video_to_keyframe_paths_map


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

    reference_directory = Path(args.reference_fingerprints_directory)
    reference_keyframes = list_reference_keyframes(reference_directory, glob_pattern)
    logger.debug(f'Found {len(reference_keyframes.keys())} reference videos in "{reference_directory}"')  # noqa: E501
