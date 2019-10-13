Video Reuse Detector
===

## What is it?

The Video Reuse Detector will allow a user to upload a video and compare
it against a set of other videos, returning a subset of those videos ranked
by their similarity to the uploaded video.

The intention is that a match should be returned even if the source video
has been exposed to some form of an "attack", such as horizontal flipping,
frame rate changes, picture-in-picture, etc.

It does this by computing video fingerprints for all of the  reference
videos, and the input video, and comparing these fingerprints against one
another. It is the fingerprints that "resistant" against these attacks.

## What is the purpose?

The project "European History Reloaded: Circulation and Appropriation of
Digital Audiovisual Heritage" (**CADEAH**)—funded by the European Union's
Horizon 2020 Research and Innovation programme --- will shed light on how
online users engage with Europe's audiovisual heritage online.

The project is a follow up on the EUscreen projects, and particularly looks
at online circulation and appropriation of audiovisual heritage via the
usage of algorithmic tracking and tracing technologies. The project brings
together scholars and developers from Utrecht University, the Institute of
Contemporary History (Czech Republic) and the digital humanities hub, Humlab
at Umeå University --- and also includes the Netherlands Institute for Sound
and Vision as a cooperation partner.

Within the media-content industry, video fingerprints are used to track
copyrighted video material. But whereas the industry seeks to police and
control piracy, CADEAH will use similar digital methods to analyse,
research and discuss the cultural dynamics around re-use and remix
of audiovisual heritage and archival footage.

## Set-up

### Prerequisites

+ `pip3`
+ `ffmpeg` 

### Set-up for development and running it

Assuming you are running on a \*nix-distro or the Windows Linux Subsystem
(WSL) the following sequence of commands should be adequate for you to try
the software out,

```
$ make init # This sets you up with the Python environment that is needed
$ make process INPUT_FILE=path/to/some/video/file
$ make process INPUT_FILE=path/to/some/other_video/file
```

(`$` is the terminal-prompt, don't type this)

now, if you inspect the `processed` directory you will find the 
video-fingerprints for the two videos in those two directories
and then lastly to compare the pair to one another execute,

```
$ make run QUERY_VIDEO=processed/video REFERENCE_VIDEO=processed/other_video
```

#### Example: comparing Megamind.avi to Megamind\_bugy.avi

Run `make opencv` to download the video files. Afterwards, run

```
$ make raw/Megamind.avi
$ make raw/Megamind_bugy.avi
```

to "create" the video-files. Continue by fingerprinting them, like so

```
$ make process INPUT_FILE=raw/Megamind.avi
$ make process INPUT_FILE=raw/Megamind_bugy.avi
```

Note: if you find the application to output more log-info than what 
interests you you can append `LOGURU_LEVEL=INFO` to your `.env` file
in the project directory to get rid of the debug statements issued
by the Python code (this is not supported by the supporting bash-scripts
yet).

And then, lastly, to run the video compare functionality, execute

```
$ make run QUERY_VIDEO=processed/Megamind REFERENCE_VIDEO=processed/Megamind_bugy
```

wherein the output is on the form,

```
0 [(0, 0.9526331845275973), (1, 0.9282540191684316), (2, 0.9010227076271993), (4, 0), (5, 0)]
1 [(0, 0.9537532553041235), (1, 0.9474603230214358), (2, 0.9171070897693965), (4, 0), (5, 0)]
2 [(1, 0.9747870768144995), (2, 0.9497378517630837), (0, 0.8716144310038891), (4, 0), (5, 0)]
...
```

where the numbers in the left-most column is the segment id in the query video, and
the list that follows are tuples of the form `(segment_id, similarity_score)` in the
reference video, i.e. segment 0 (the first second) in `Megamind.avi` is 95% similar
to the segment 0 (the first second) in `Megamind_bugy.avi`. Meanwhile, the third
segment (id=2) in `Megamind.avi` is 97% similar to the second segment (id=1) in
`Megamind_bugy.avi`.


### Why this value, why this algorithm?

This code implements the fingerprinting method proposed by Zobeida Jezabel
Guzman-Zavaleta in the thesis "An Effective and Efficient Fingerprinting Method
for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis,
specifically from the section 5.4 Discussion, where the author details the
parameter values that "proved" the "best" during her experiments.
