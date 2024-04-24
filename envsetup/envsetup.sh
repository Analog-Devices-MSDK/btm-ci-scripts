#!/bin/bash
# MUST RUN AS SUDO!
set -e
source /home/btm-ci/.bashrc
envcheck 4 CI_BOARD_CONFIG RESOURCE_LOCK_DIR RESOURCE_SHARE_DIR OPENOCD_PATH
set +e

env="LANG=en_US.UTF-16"
printf '%s\n' \
    $env \
    "CI_BOARD_CONFIG=$CI_BOARD_CONFIG" \
    "RESOURCE_LOCK_DIR=$RESOURCE_LOCK_DIR" \
    "RESOURCE_SHARE_DIR=$RESOURCE_SHARE_DIR" \
    "OPENOCD_PATH=$OPENOCD_PATH" \
    > .env

for i in {0..3}; do
cp .env /home/btm-ci/Workspace/btm-ci-github-runner$i
cd /home/btm-ci/Workspace/btm-ci-github-runner$i && ./svc.sh stop
cd /home/btm-ci/Workspace/btm-ci-github-runner$i && ./svc.sh start
done



rm .env
