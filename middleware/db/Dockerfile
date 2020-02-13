# pull official base image
FROM postgres:11.4-alpine

LABEL maintainer="Humlab <support at humlab dot umu dot se>"
LABEL description="Postgres database for Video Reuse Detector"

# run create.sql on init
ADD create.sql /docker-entrypoint-initdb.d
