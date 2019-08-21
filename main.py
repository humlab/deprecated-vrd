import cv2

"""
This code implements the fingerprinting method proposed by Zobeida Jezabel Guzman-Zavaleta
in the thesis "An Effective and Efficient FingerprintingMethod for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis, specifically
from the section 5.4 Discussion, where the author details the parameter values that "proved"
the "best" during her experiments.
"""

def divide_into_segments(filename, segment_length_in_seconds=1):
    import subprocess

    ffmpeg_cmd = (
        f'ffmpeg -i {filename}'                       # input file
          ' -codec:v libx264'                         # re-encode to overwrite keyframes
        f' -force_key_frames expr:gte(t,n_forced*{segment_length_in_seconds})'
         ' -map 0'                                    # use the first input file for all outputs
         ' -f segment'                                # output file will be multiple segments
        f' -segment_time {segment_length_in_seconds}' # length of each segment expressed in seconds
         ' output%03d.mp4'
         )

    subprocess.call(ffmpeg_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def downsample_video(path_to_video_file, fps=5):
    """
    Assumes that the given path refers to a video file and extracts an `fps` number of frames
    from every second of the specified video.

    For instance, for a video "video.mp4" `downsample_video('video.mp4', fps=5)` will yield 5 frames
    for every second of said video. If said video is, for instance, 10 seconds long, the number of
    frames that are produced is equal to 50.

    This function does not have a return value, but has a side-effect, namely a series of image files
    (.png) whose names are on the form `{path_to_video_file}-frame%d.png`, where the file extension
    is removed from the `path_to_video_file` parameter.
    """
    import subprocess
    from pathlib import Path

    video_path = Path(path_to_video_file)
    video_filename = video_path.stem
    directory = video_path.parent

    subprocess.call(f'ffmpeg -i {path_to_video_file} -vf fps={fps} {directory}/{video_filename}-frame%d.png'.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def scale_image(image, scale_factor):
    height, width, _ = image.shape

    # Another option, which is slower, would be INTER_CUBIC, which would "look" the "best"
    interpolation_method = cv2.INTER_LINEAR if scale_factor >= 1 else cv2.INTER_AREA
    return cv2.resize(img, (width*scale_factor, height*scale_factor), interpolation=interpolation_method)

def crop(image, m=320, n=320):
    height, width, _ = image.shape

    ch, cw = int(height/2), int(width/2)
    sx = int(cw - m/2)
    sy = int(ch - n/2)

    img = image[sy:sy+n, sx:sx+m]

    return img