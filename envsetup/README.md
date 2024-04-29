# ENVSETUP

In order for GitHub to be able to access the environment variables when ran on the CI machine, the .env files need to be populated.
``evsetup.sh`` will generate the file and deploy it to the CI directories. As well as do the stop/start process for the runner service.

NOTE: This script is only useful for the CI, not your local machine. You will need to add your variables to the bashrc manually, as shown in the main README.

## Permissions
- The script needs to be ran as sudo since the runner service needs to be stopped and started running as root.

## Adding new variables
Add any new variables like the ones already shown inside envsetup.
```
printf '%s\n' \
    $env \
    "CI_BOARD_CONFIG=$CI_BOARD_CONFIG" \
    "RESOURCE_LOCK_DIR=$RESOURCE_LOCK_DIR" \
    "RESOURCE_SHARE_DIR=$RESOURCE_SHARE_DIR" \
    "OPENOCD_PATH=$OPENOCD_PATH" \
    > .env
```
Please do not manually write the path. The reason it is done this way is to keep synchronization on the machine and to add some basic security. 
