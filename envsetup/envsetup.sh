#!/bin/bash
# MUST RUN AS SUDO!

is_not_running_as_root() {
    [[ $EUID -ne 0 ]]
}

if is_not_running_as_root; then
    echo "Script must be ran using sudo!"
    exit -1
fi

source /home/btm-ci/.bashrc

env="LANG=en_US.UTF-16"
printf '%s\n' \
    $env \
    "CI_BOARD_CONFIG=$CI_BOARD_CONFIG" \
    "RESOURCE_LOCK_DIR=$RESOURCE_LOCK_DIR" \
    "RESOURCE_SHARE_DIR=$RESOURCE_SHARE_DIR" \
    "OPENOCD_PATH=$OPENOCD_PATH" \
    "TEST_DIR=$TEST_DIR" \
    "CI_CONFIG_DIR=$CI_CONFIG_DIR" \
    "PATH=$PATH"\
    >.env


set -e
for i in {0..3}; do
    cp .env /home/btm-ci/Workspace/btm-ci-github-runner$i
    (cd /home/btm-ci/Workspace/btm-ci-github-runner$i && ./svc.sh stop)
    (cd /home/btm-ci/Workspace/btm-ci-github-runner$i && ./svc.sh start)
    
done

cp .env /home/btm-ci/Workspace/adi-msdk-github-runner0
(cd /home/btm-ci/Workspace/adi-msdk-github-runner0 && ./svc.sh stop)
(cd /home/btm-ci/Workspace/adi-msdk-github-runner0 && ./svc.sh start)
