# MUST RUN AS SUDO!

env="LANG=en_US.UTF-16"
printf '%s\n' \
    $env \
    "CI_BOARD_CONFIG=$CI_BOARD_CONFIG" \
    "RESOURCE_LOCK_DIR=$RESOURCE_LOCK_DIR" \
    "OPENOCD_PATH=$OPENOCD_PATH" \
    > .env
cp .env ~/Workspace/btm-ci-github-runner0
cp .env ~/Workspace/btm-ci-github-runner1
cp .env ~/Workspace/btm-ci-github-runner2
cp .env ~/Workspace/btm-ci-github-runner3

rm .env

./~/Workspace/btm-ci-github-runner0/svc.sh stop
./~/Workspace/btm-ci-github-runner1/svc.sh stop
./~/Workspace/btm-ci-github-runner2/svc.sh stop
./~/Workspace/btm-ci-github-runner3/svc.sh stop

./~/Workspace/btm-ci-github-runner0/svc.sh start
./~/Workspace/btm-ci-github-runner1/svc.sh start
./~/Workspace/btm-ci-github-runner2/svc.sh start
./~/Workspace/btm-ci-github-runner3/svc.sh start
