# btm-ci-scripts
The point of these scripts is to make the most annoying parts of CI go away
On WALLE, 
btm-ci-scripts is located at ```~/Tools```  

## WALLE Environment Variables
```
chmod +x /home/btm-ci/Tools/btm-ci-scripts/Resource_Share/resource_manager.py
export PATH=$PATH:/home/btm-ci/Tools
export PATH=$PATH:/home/btm-ci/Tools/JLink_Linux_V780c_x86_64
export PATH="$PATH:/home/btm-ci/Tools/btm-ci-scripts"
export PATH="$PATH:/home/btm-ci/Tools/btm-ci-scripts/Resource_Share"
export CI_BOARD_CONFIG=/home/btm-ci/Tools/btm-ci-scripts/Resource_Share/boards_config.json
export RESOURCE_LOCK_DIR=/home/btm-ci/Tools/btm-ci-scripts/Resource_Share/Locks
export OPENOCD_PATH=/home/btm-ci/Tools/openocd
source virtualenvwrapper.sh
source /home/btm-ci/Tools/btm-ci-scripts/flash-utils.sh
```
This setup in the .bashrc gives access to ocdflash, ocderase, resource_manager.py, BOARD_CONFIG_PATH, RESOURCE_LOCK_DIR, and OPENOCD path. Others will be added as time goes on.


## ocdflash
- Flash a board given the resource board name and the path to the elf file
- Example: ```ocdflash max32655_board1 ~/msdk/Examples/BLE5_ctr/build/max32655.elf```

 ## ocderase
 - Erase a board in the resource board name
 - Example: ```ocderase max32655_board1```

## resource_manager.py
Resource manager handles locking/unlock boards, monitoring usage, and getting information about the boards. 
```
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


## Past lessons learned and moving forward
- Pathing is incredibly easy to mess up in yaml files. So all commonly used fucntions are now global.
- Bash is easy to mess up and no one on our team is very good at it. Simple bash only
- If you find yourself using loops or arrays in bash it is time to use python or some other language like golang.
- If your test runs on walle, put it in the the btm-ci scripts folder. No need to add to the tangled mess that is the workflows.
- Keep workflows as flat as possible. Tracking dependencies is difficult.
- If you find yourself doing a very common thing. Make it a script and put it into the btm-ci-scripts
