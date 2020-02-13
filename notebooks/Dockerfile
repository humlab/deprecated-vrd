ARG BASE_CONTAINER=jupyter/minimal-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Humlab <support at humlab dot umu dot se>"
LABEL description="Notebooks for Video Reuse Detector"

USER jovyan

# Notebook lab packages 
RUN conda install --quiet --yes \
    'conda-forge::jupytext' \
    'conda-forge::blas=*=openblas' \
    'ipywidgets=7.5*' \
    'matplotlib-base=3.1.*' \
    && \
    conda clean --all -y && \
    # Activate ipywidgets extension in the environment that runs the notebook server
    jupyter nbextension enable --py widgetsnbextension --sys-prefix && \
    # Also activate ipywidgets extension for JupyterLab
    jupyter labextension install @jupyter-widgets/jupyterlab-manager@^1.0.1 --no-build && \
    # Activate jupytext in the environment that runs the notebook server
    jupyter nbextension enable jupytext --py --sys-prefix && \
    jupyter lab build && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf /home/$NB_USER/.cache/yarn && \
    rm -rf /home/$NB_USER/.node-gyp && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

RUN conda upgrade conda -y

# Import matplotlib the first time to build the font cache.
ENV XDG_CACHE_HOME /home/$NB_USER/.cache/
RUN MPLBACKEND=Agg python -c "import matplotlib.pyplot" && \
    fix-permissions /home/$NB_USER

COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

RUN pip install pandas && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

USER root

# ffmpeg for video segmentation
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libgavl1 frei0r-plugins && \
    rm -rf /var/lib/apt/lists/*
