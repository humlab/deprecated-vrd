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
# # Compare FingerprintComputationComparison Processing Data
#
# In this notebook we compare performance data between CSV-files for processing time with regards to computing fingerprints.

# %%
import os
from pathlib import Path
import datetime

BENCHMARKS_DIRECTORY = Path(os.environ['BENCHMARKS_DIRECTORY'])

prev_computation = BENCHMARKS_DIRECTORY / 'Fingerprint_Collection_Computation_2020-02-22_08-12-11.csv'

# Note: this values are fake and are just to show how to graph any performance improvement/regression
new_computation = BENCHMARKS_DIRECTORY / 'Fingerprint_Collection_Computation_2020-02-22_08-12-11_mock.csv'

assert prev_computation != new_computation

# %% [markdown]
# And then we plot the data. First, as a bar chart for each respective video,

# %%
import pandas as pd
import matplotlib.pyplot as plt

before_df = pd.read_csv(str(prev_computation))
before_df = df.sort_values(by=['Video Duration'], ascending=[True])

after_df = pd.read_csv(str(new_computation))
after_df = df.sort_values(by=['Video Duration'], ascending=[True])

before_df.set_index('Video Duration')['Processing Time'].plot()
after_df.set_index('Video Duration')['Processing Time'].plot()

plt.legend([prev_computation.name, new_computation.name])
plt.ylabel('Processing Time')
plt.xlabel('Video Duration')
plt.axes().xaxis.grid(True)
plt.show()

# %%
