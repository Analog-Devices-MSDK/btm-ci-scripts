# btm-ci-scripts

The point of these scripts is to make the most annoying parts of CI go away

On WALLE,
btm-ci-scripts is located at ```~/Tools```  

## WALLE Environment Variables

```bash
export PATH=$PATH:/home/btm-ci/Tools
export PATH="$PATH:/home/btm-ci/Tools/btm-ci-scripts"
export CI_BOARD_CONFIG=<PATH TO CI BOARD CONFIG>
export CI_BOARD_CONFIG_CUSTOM=<PATH TO CUSTOM CONFIG>
export RESOURCE_LOCK_DIR=/home/btm-ci/Tools/btm-ci-scripts/Resource_Share/Locks
export OPENOCD_PATH=/home/btm-ci/Tools/openocd
export RESOURCE_FILES="$CI_BOARD_CONFIG_CUSTOM"
export RESOURCE_FILES="$CI_BOARD_CONFIG:my_extra_config.json"
```

## Resource Manager

Resource manager handles locking/unlock boards, monitoring usage, and getting information about the boards. OpenOCD utils are also included. It is already installled on WALLE, but is very useful for development on your local machine. For instructions on installation and usage of these tools please look [here](Resource_Share/README.md)

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
- If your test runs on walle, put it in the the btm-ci scripts folder to test. Then if needed move it to the repo it belongs with if needed.
- Test the workflows in the btm-ci-scripts repo before deploying it to other repos first.
- Keep workflows as flat as possible. Tracking dependencies is difficult.
- If you find yourself doing a very common thing. Make it a script and put it into the btm-ci-scripts
