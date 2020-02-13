FROM python:3.7.2-slim

LABEL maintainer="Humlab <support at humlab dot umu dot se>"
LABEL description="Application middleware for Video Reuse Detector"

RUN apt-get update -y && \
    apt-get install netcat-openbsd -y && \
    apt-get install ffmpeg -y && \
    apt-get install gcc -y && \
    apt-get clean

WORKDIR /usr/src/app

# Prevents Python from writing pyc files to disc.
# Equivalent to executing python -B. 
#
# See https://docs.python.org/3/using/cmdline.html#id1 
ENV PYTHONDONTWRITEBYTECODE 1

# Install pipenv
RUN pip install --upgrade pip && pip install --no-cache-dir --trusted-host pypi.python.org pipenv
COPY ./Pipfile .
RUN pipenv install --skip-lock --system --dev

COPY ./middleware/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENV PYTHONPATH /usr/src/app:$PYTHONPATH

COPY . .
