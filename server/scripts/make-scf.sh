#!/usr/bin/env bash

set -e

[ -z "${PYPI_INDEX_URL}" ] && PYPI_INDEX_URL=https://mirrors.aliyun.com/pypi/simple

docker run -it --rm \
    -u $(id -u ${USER}):$(id -g ${USER}) \
    -v "$(dirname $(pwd)):/var/project" \
    -v "$(python3 -m pip cache dir):/tmp/pip-cache" \
    quay.io/pypa/manylinux2014_x86_64 \
    /bin/sh -c \
    "
    set -e
    export TARGET_DIR=$(mktemp -d)
    export TARGET_FILE=/var/project/server/dist/scf-$(git describe).zip
    (
        cd /var/project/server
        python3.7 -m pip install --disable-pip-version-check --cache-dir /tmp/pip-cache \
            -r requirements.txt -t \$TARGET_DIR \
            $([ -n "${PYPI_INDEX_URL}" ] && echo "-i ${PYPI_INDEX_URL}")
        cp -av scf_bootstrap app.py views.py utils.py \$TARGET_DIR
        cp -av config.production.py \$TARGET_DIR/config.py
        mkdir -p \$TARGET_DIR/templates
        cp -av ../client/index.html \$TARGET_DIR/templates
    )
    (
        cd \$TARGET_DIR
        mkdir -p /var/project/dist
        [ -f \$TARGET_FILE ] && rm -fv \$TARGET_FILE
        echo \"compress to ‘\${TARGET_FILE}’\"
        python3.7 -m zipfile -c \$TARGET_FILE *
    )
    "
