FROM python:3.7.0-alpine

LABEL maintainer="Humlab <support at humlab dot umu dot se>"
LABEL description="Dashboard for Video Reuse Detector"

RUN pip install rq-dashboard

EXPOSE 9181

CMD ["rq-dashboard"]
