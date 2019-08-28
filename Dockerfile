ARG BASE_CONTAINER=jupyter/minimal-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Humlab <support@humlab.umu.se>"

USER root

# ffmpeg for video segmentation
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

USER $NB_UID

# Notebook lab packages 
RUN conda install --quiet --yes \
    'matplotlib-base=3.1.*' \
    'scikit-image=0.15*' \
    'scipy=1.3*' \
    && \
    conda clean --all -y && \
    jupyter lab build && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf /home/$NB_USER/.cache/yarn && \
    rm -rf /home/$NB_USER/.node-gyp && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER
