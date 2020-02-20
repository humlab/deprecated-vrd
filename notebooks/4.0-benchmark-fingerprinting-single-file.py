# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Benchmark Fingerprinting (single file)
#
# Note: this notebook requires an active deployment of the app.
#     
# We begin by checking that the app is running,

# %%
import os
import requests

REACT_APP_API_URL = os.environ['REACT_APP_API_URL']
url = f"{REACT_APP_API_URL}/api/ping"
response = requests.get(url)

assert response.status_code == 200
assert response.json()['message'] == 'pong'
response.json()

# %% [markdown]
# And then we proceed to prepare a file for uploading so that it can be fingerprinted,

# %%
from pathlib import Path
import shutil # To copy files
import video_reuse_detector.ffmpeg as ffmpeg  # Optional, if we want shorter files we can use ffmpeg.slice
import datetime

# Uploading a file will trigger fingerprint computation eventually, and
# assuming the application is not under load, it will happen immediately
VIDEO_DIRECTORY = Path(os.environ['VIDEO_DIRECTORY'])
assert VIDEO_DIRECTORY.exists()
print(f"VIDEO_DIRECTORY={VIDEO_DIRECTORY}")

OUTPUT_DIRECTORY = Path(os.environ['OUTPUT_DIRECTORY'])
print(f"OUTPUT_DIRECTORY={OUTPUT_DIRECTORY}")

# This video might be uploaded already, so we should create a copy with a different name.
# This is because the backend checks for "uniqueness" of videos by referring to the
# filename (post-sanitation)
reference_video_path = VIDEO_DIRECTORY / 'panorama_augusti_1944.mp4'
assert(reference_video_path.exists())

to_benchmark = ffmpeg.slice(reference_video_path, "00:01:30", "00:02:00", OUTPUT_DIRECTORY)
assert(to_benchmark.exists())

extension = reference_video_path.suffix  # contains the leading "." before the extension
print(f"extension={extension}")

timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
print(f"timestamp={timestamp}")

# We'll store the copy there, this is the target path
to_be_uploaded = OUTPUT_DIRECTORY / f"{to_benchmark.stem}_{timestamp}{extension}"

# Copy the file from the original path to the target path
shutil.copy(str(to_benchmark), str(to_be_uploaded))


# %% [markdown]
# The file which `to_be_uploaded` references may now be uploaded. The following function can be used to upload a file to the application,

# %%
def upload_query_file(file_path, file_type='QUERY'):
    data = {'file_type': file_type}
    files = {'file': open(str(file_path), 'rb')}

    url = f"{REACT_APP_API_URL}/api/files/upload"

    print(f"Issuing POST-request with data={data}, with {file_path} as content to {url}")
    return requests.post(url, data=data, files=files)


# %% [markdown]
# Before uploading the file, we prepare a CSV-file to contain the benchmark data. We will seed the name of the CSV-file using the file that we upload,

# %%
BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

benchmarks_csv = f"fingerprint_benchmarks_{to_be_uploaded.name}.csv"
benchmarks_csv = BENCHMARKS_DIRECTORY / benchmarks_csv
benchmarks_csv.parent.mkdir(parents=True, exist_ok=True)
print(f"benchmarks_csv={benchmarks_csv}")

# %% [markdown]
# Before uploading the file, we prepare a socket connection to be notified when the fingerprint has been computed.

# %%
import socketio

sio = socketio.Client()


# %% [markdown]
# And we specify what we want to do when notified by the backend that the fingerprint has been computed. What do we want to do? We want to log to our CSV-file the time it took to create the fingerprint. How do we do this? After the socket has been notified, we can take the time delta between `created_on` and `updated_on` to discern how long the fingerprinting process took.

# %%
def convert_backend_timestamp(time_str):
    from datetime import datetime
    
    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')
    
@sio.on('video_file_fingerprinted')
def on_fingerprinted(video_file_info):
    video_that_has_been_fingerprinted = video_file_info['video_name']
    print(f"{video_that_has_been_fingerprinted} fingerprinted!")

    if video_that_has_been_fingerprinted != to_be_uploaded.name:
        print("Another file other than our upload was fingerprinted. Keeping socket open")
        return
    
    assert video_file_info['processing_state'] == 'FINGERPRINTED'

    created_on = convert_backend_timestamp(video_file_info['created_on'])
    updated_on = convert_backend_timestamp(video_file_info['updated_on'])

    processing_time = updated_on - created_on
    
    with open(str(benchmarks_csv), 'w') as f:
        header = 'Name,Processing_Time'
        print(f'Writing header="{header}" to csv-file')
        f.write(f'{header}\n')
    
        video_name = video_file_info['video_name']
        content = f"{video_name},{processing_time.total_seconds()}"
        print(f'Writing "{content}" to csv-file')
        f.write(f"{content}\n")
    
    # We disconnect after to return control to Jupyter
    sio.disconnect()


# %% [markdown]
# Let's prepare our socket connection a little further, to get an acknowledgement when the connection has successfully been setup,

# %%
@sio.on('connect')
def on_connect():
    print("I'm connected to the default namespace!")


# %% [markdown]
# We now upload the file, and hand-over control to the socket, which will return control to Jupyter after the video has been fingerprinted. 

# %%
# And finally upload the newly created file
print(upload_query_file(to_be_uploaded).text)

def fetch_file_info(filename):
    # Include the extension with the filename!
    return requests.get(f"{REACT_APP_API_URL}/api/files/{filename}")

json = fetch_file_info(to_be_uploaded.name).json()
print(json)

assert json['file']['processing_state'] == 'UPLOADED'
print(json)

sio.connect("http://dev.humlab.umu.se:8082")    
print('my sid is', sio.sid)
sio.wait()  # This is blocking

print('End')
