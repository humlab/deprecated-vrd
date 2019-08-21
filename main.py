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
