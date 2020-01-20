#!/usr/bin/env bash

ESLINT="$(git rev-parse --show-toplevel)/frontend/node_modules/.bin/eslint"

# Check for eslint
if [[ ! -x "$ESLINT" ]]; then
  printf "\t\033[41mPlease install ESlint\033[0m (run npm i inside the \"frontend\"-directory)"
  exit 1
fi

npm run lint --prefix frontend
