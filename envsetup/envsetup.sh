# MUST RUN AS SUDO!

env="LANG=en_US.UTF-16"
printf '%s\n' \
    $env \
    "CI_BOARD_CONFIG=$CI_BOARD_CONFIG" \
    "RESOURCE_LOCK_DIR=$RESOURCE_LOCK_DIR" \
    "RESOURCE_SHARE_DIR=$RESOURCE_SHARE_DIR" \
    "OPENOCD_PATH=$OPENOCD_PATH" \
    > .env



# for i in {0..3}; do
# cp .env ~/Workspace/btm-ci-github-runner$i
# ./~/Workspace/btm-ci-github-runner${i}/svc.sh stop
# ./~/Workspace/btm-ci-github-runner${i}/svc.sh start
# done

cp .env ~/Workspace/btm-ci-github-runner0
cp .env ~/Workspace/btm-ci-github-runner1
cp .env ~/Workspace/btm-ci-github-runner1
cp .env ~/Workspace/btm-ci-github-runner3


./~/Workspace/btm-ci-github-runner0/svc.sh stop
./~/Workspace/btm-ci-github-runner1/svc.sh stop
./~/Workspace/btm-ci-github-runner2/svc.sh stop
./~/Workspace/btm-ci-github-runner3/svc.sh stop

./~/Workspace/btm-ci-github-runner0/svc.sh start
./~/Workspace/btm-ci-github-runner1/svc.sh start
./~/Workspace/btm-ci-github-runner2/svc.sh start
./~/Workspace/btm-ci-github-runner3/svc.sh start

rm .env
