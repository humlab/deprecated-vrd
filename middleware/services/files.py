from typing import Dict

from ..models import db
from ..models.video_file import VideoFile


def list_files() -> Dict[str, str]:
    query = db.session.query(VideoFile.video_name, VideoFile.processing_state)

    # This is a list of two-element tuples, (video_name, processing_state)
    list_of_tuples = list(query)

    # Unpack the single-element tuples, transforming
    #
    # [('some_name.avi', 'FINGERPRINTED'),...]
    #
    # into a dictionary on the form {'some_name.avi': 'FINGERPRINTED',...}
    #
    # Note that the states are in an enum representation, hence .name
    d = {t[0]: t[1].name for t in list_of_tuples}

    return d
