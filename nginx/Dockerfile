FROM nginx:1.15.8-alpine

LABEL maintainer="Humlab <support at humlab dot umu dot se>"
LABEL description="Nginx-proxy for Video Reuse Detector"

RUN rm /etc/nginx/conf.d/default.conf
COPY /dev.conf /etc/nginx/conf.d
