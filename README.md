# btm-ci-scripts

The point of these scripts is to make the most annoying parts of CI go away
On WALLE,
btm-ci-scripts is located at ```~/Tools```  

## WALLE Environment Variables

```bash
export PATH=$PATH:/home/btm-ci/Tools
export PATH=$PATH:/home/btm-ci/Tools/JLink_Linux_V780c_x86_64
export PATH="$PATH:/home/btm-ci/Tools/btm-ci-scripts"
export CI_BOARD_CONFIG=<PATH TO CI BOARD CONFIG>
export CI_BOARD_CONFIG_CUSTOM=<PATH TO CUSTOM CONFIG>
export RESOURCE_LOCK_DIR=/home/btm-ci/Tools/btm-ci-scripts/Resource_Share/Locks
export OPENOCD_PATH=/home/btm-ci/Tools/openocd
source /home/btm-ci/Tools/btm-ci-scripts/shell-scripts/flash-utils.sh
export RESOURCE_FILES="$CI_BOARD_CONFIG_CUSTOM"
export RESOURCE_FILES="$CI_BOARD_CONFIG:my_extra_config.json"
```

This setup in the .bashrc gives access to ocdflash, ocderase, resource_manager.py, BOARD_CONFIG_PATH, RESOURCE_LOCK_DIR, and OPENOCD path. Others will be added as time goes on.

## OPENOCD_PATH

Openocd commands will try to use the scripts folder. This path needs to point to the base of openocd where scripts is.

## ocdflash

- Flash a board given the resource board name and the path to the elf file
- Example: ```ocdflash max32655_board1 ~/msdk/Examples/BLE5_ctr/build/max32655.elf```

## ocderase

- Erase a board in the resource board name
- Example: ```ocderase max32655_board1```

## resource_manager

Resource manager handles locking/unlock boards, monitoring usage, and getting information about the boards.

### Installation

Navigate to the ``Resource_Share`` folder inside the btm-ci-scripts repo and run the ``install.sh`` script

The script will be installed to your python site packages and accessible via the command line by running ``resource_manager``

```bash
btm-ci@wall-e:~$ resource_manager.py -h
usage: resource_manager.py [-h] [--custom-config CUSTOM_CONFIG] [--timeout TIMEOUT] [-u [UNLOCK [UNLOCK ...]]] [--unlock-all]
                           [-l [LOCK [LOCK ...]]] [--list-usage] [-g GET_VALUE]

    Lock/Unlock Hardware resources
    Query resource information
    Monitor resources
    

optional arguments:
  -h, --help            show this help message and exit
  --custom-config CUSTOM_CONFIG
                        Custom config for boards. Will be added to what is on CI
  --timeout TIMEOUT, -t TIMEOUT
                        Timeout before returning in seconds
  -u [UNLOCK [UNLOCK ...]], --unlock [UNLOCK [UNLOCK ...]]
                        Name of board to unlock per boards_config.json
  --unlock-all          Unlock all resources in lock directory
  -l [LOCK [LOCK ...]], --lock [LOCK [LOCK ...]]
                        Name of board to lock per boards_config.json
  --list-usage          Display basic usage stats of the boards including if they are locked and when they were locked
  -g GET_VALUE, --get-value GET_VALUE
                        Get value for resource in config (ex: max32655_board1.dap_sn)

```

## BOARD_CONFIG_PATH

Path to board config, which contains all needed information to flash and communicate with DUTs

## Custom Board config path

Optionally, you can add a custom board config by exporting its path equal to CI_BOARD_CONFIG_CUSTOM

## RESOURCE_LOCK_DIR

Directory where lockfiles for boards are stored

## OPENOCD PATH

Path to where the openocd tooling is located

## Getting the environment variables loaded for GitHub Workflows

The environment variables loaded into the bashrc will not be sourced by GitHub. These can only be used for manual usage.
The variables need to be placed into the ``.env`` files located in the runner directories on Wall-E.
For convenience, the ``envsetup.sh``, located in the envsetup folder, can be ran on Wall-E. This will automatically load the .env file into the runner.

## Actions

In order to make some of the common tasks reliable and easy to use, we have created some basic actions that can perform these tasks.
More information can be found in the ``actions`` folder.

Some actions include

- Locking/Unlocking resources
- Resetting, flashing, and erasing boards

## Past lessons learned and moving forward

- Pathing is incredibly easy to mess up in yaml files. So all commonly used fucntions are now global.
- Bash is easy to mess up in a workflow. Simple bash only.
- If you find yourself using loops or arrays in bash it is time to use python or some other language like golang.
- If your test runs on walle, put it in the the btm-ci scripts folder.
- Test the workflows in the btm-ci-scripts repo before deploying it to other repos first.
- Keep workflows as flat as possible. Tracking dependencies is difficult.
- If you find yourself doing a very common thing. Make it a script and put it into the btm-ci-scripts
