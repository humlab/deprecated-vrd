FROM node:latest

WORKDIR /usr/src/app

LABEL maintainer="Humlab <support at humlab dot umu dot se>"
LABEL description="Frontend for Video Reuse Detector"

ENV PATH /usr/src/app/node_modules/.bin:$PATH
ENV REACT_APP_API_URL $REACT_APP_API_URL

COPY package.json /usr/src/app/package.json
COPY package-lock.json /usr/src/app/package-lock.json
RUN npm ci
RUN npm install react-scripts@3.0.1 -g --silent

CMD ["npm", "start"]
