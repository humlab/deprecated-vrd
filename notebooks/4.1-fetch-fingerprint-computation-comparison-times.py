# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Fetches FingerprintComputationComparison Processing Data
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
# And then we proceed to slurp out all the available fingerprint computation execution time data,

# %%
from pathlib import Path
import datetime

BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

csv_response = requests.get(f"{REACT_APP_API_URL}/admin/fingerprintcollectioncomputation/export/csv")
filename = csv_response.headers['Content-Disposition'].split('filename=')[1]

csv_file = BENCHMARKS_DIRECTORY / filename
with open(csv_file, 'wb') as f:
    f.write(csv_response.content)
    
print(f"Results stored in {str(csv_file)}")

# %% [markdown]
# And then we plot the data. First, as a bar chart for each respective video,

# %%
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(str(csv_file))
df = df.sort_values(by=['Video Duration'], ascending=[True])
df.set_index('Video Name', inplace=True, drop=True)
ax = df.plot.barh(figsize=(len(df), 18))

plt.xlabel('seconds')
plt.axes().xaxis.grid(True)
plt.show()

# %% [markdown]
# And then processing time as a function of video duration,

# %%
df.set_index('Video Duration')['Processing Time'].plot()

plt.ylabel('Processing Time')
plt.show()
