#!/usr/bin/env bash

set -e

export SITE_PATH=demo/trtc/web
rm -rf dist/$SITE_PATH/*

mkdir -p dist/$SITE_PATH/app
cp -av css data img js dist/$SITE_PATH/app
cp -av env.production.js dist/$SITE_PATH/app/env.js

npm run docs:build
mkdir -p dist/$SITE_PATH/docs
cp -av docs/.vuepress/dist/* dist/$SITE_PATH/docs
