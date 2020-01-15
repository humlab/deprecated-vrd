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
Digital Audiovisual Heritage" (**CADEAH**) --- funded by the European Union's
Horizon 2020 Research and Innovation programme --- will shed light on how
online users engage with Europe's audiovisual heritage online.

The project is a follow up on the EUscreen-projects, and particularly looks
at online circulation and appropriation of audiovisual heritage via the
usage of algorithmic tracking and tracing technologies. The project brings
together scholars and developers from Utrecht University, the Institute of
Contemporary History (Czech Republic) and the digital humanities hub, Humlab,
at Umeå University --- and also includes the Netherlands Institute for Sound
and Vision as a cooperation partner.

Within the media-content industry, video fingerprints are used to track
copyrighted video material. But whereas the industry seeks to police and
control piracy, **CADEAH** will use similar digital methods to analyse,
research and discuss the cultural dynamics around re-use and remix
of audiovisual heritage and archival footage.

## Set-up

### Prerequisites

+ `docker`
+ `make`

And to run things locally without spinning up containers,

+ `python3.7`, 
+ `pip3`,
+ `pipenv`,
+ and `ffmpeg`

**Tip:** run `make help` to see what targets are available, the content below might be out-of-date:

```
black-check                    Dry-run the black-formatter on Python-code with the --check option, doesn't normalize single-quotes
black-diff                     Dry-run the black-formatter on Python-code with the --diff option, doesn't normalize single-quotes
black-fix                      Run the black-formatter on Python-code, doesn't normalize single-quotes. This will change the code if "make black-check" yields a non-zero result
build-images                   Builds the docker images
connect-to-db                  Access database through psql. Use \c video_reuse_detector_dev or \c video_reuse_detector_test to connect to either database. Use \dt to describe the tables
doctest                        Execute doctests for Python-code
down                           Bring down the containers
forcebuild                     Forces a rebuild, ignoring cached layers
init                           Installs python dependencies for local development. Please install ffmpeg manually
installcheck                   Checks that dependencies are installed, if everything is okay nothing is outputted
isort                          Dry-run isort on the Python-code, checking the order of imports
isort-fix                      Run isort on the Python-code, checking the order of imports. This will change the code if "make isort" yields a non-empty result
jslint                         Run lint checks for React-application
jslint-fix                     Run lint checks for React-application and attempt to automatically fix them
lint                           Run lint checks for Python-code and the React application
mypy                           Run type-checks for Python-code
pyunittest                     Execute Python-unittests. Note, this does not run in the docker container as it won't have sufficient memory
recreate-db                    Recreate the database, nuking the contents therein
remove-images                  Forcefully remove _all_ docker images
run-containers                 Run the docker images
stop                           Stop the containers
```

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

#### Deploy notebooks

To deploy the notebook environment run `python scripts/generate_access_token.sh <SECRET>` and
set the environment variable `ACCESS_TOKEN` as per the output of the program, i.e., if you 
invoke the script thusly,

```
python scripts/generate_access_token.py cadeah
ACCESS_TOKEN=sha1:d2252fbe2d8c:a49bbe50af9669029ed6ecd88bd7baca31202085
```

then you can deploy the notebook like so (in fish)

```
begin
  set -lx ACCESS_TOKEN=sha1:d2252fbe2d8c:a49bbe50af9669029ed6ecd88bd7baca31202085
  docker-compose -f notebook.yml up --build -d
end
```

and login using "cadeah" as a password.


### Why this value, why this algorithm?

This code implements the fingerprinting method proposed by Zobeida Jezabel
Guzman-Zavaleta in the thesis "An Effective and Efficient Fingerprinting Method
for Video Copy Detection".

The default values used here can be assumed to stem from the same thesis,
specifically from the section 5.4 Discussion, where the author details the
parameter values that "proved" the "best" during her experiments.
