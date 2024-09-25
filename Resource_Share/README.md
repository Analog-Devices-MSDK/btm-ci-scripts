# Board Config and Resource Manager

## Board Config

The board config describes all hardware connected to the CI machine.

Example:

```json
"max32655_board_2" : {
    "desc"         : "marked sn #2, for per test,",
    "target"       : "MAX32655",
    "board"        : "EvKit_V1",
    "rev"          : "PCB-00177-B-0",
    "group"        : "APP",
    "dap_sn"       : "04090000ceeb82b000000000000000000000000097969906",
    "console_port" : "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D309ZDEP-if00-port0",
    "hci_port"     : "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DT03OH8D-if00-port0",
    "ocdports"     : {
        "gdb"    : "3552",
        "tcl"    : "4552",
        "telnet" : "6552"
    },
}
```

### Required Fields if programmable with openocd

- Target : Chip target as found in openocd target
- dap_sn : Serial number of dap programmer

### Optional fields

All fields are optional if they do not require the field. For example, a spectrum anaylzer does not need a board field. This can be left null in that case.
-- ocdports : Ports to flash on. If not specified the resource_manager will generate ports for you.

### Value usage

Any value can be queried using the resource manager for use in workflows, actions, and test scripts.

## Resource Manager

The resource manager is a CLI and python library tool which can be used both in other python scripts and from the command line. It's primary functions are

- Lock/Unlcock hardware resources
- Query resource information
- Monitor resources

### CLI usage

```bash
usage: resource_manager.py [-h] [--timeout TIMEOUT] [-u [UNLOCK ...]] [--unlock-all] [-l [LOCK ...]] [--owner OWNER] [--list-usage] [-g GET_VALUE] [-go GET_OWNER]

    Lock/Unlock Hardware resources
    Query resource information
    Monitor resources
    

options:
  -h, --help            show this help message and exit
  --timeout TIMEOUT, -t TIMEOUT
                        Timeout before returning in seconds
  -u [UNLOCK ...], --unlock [UNLOCK ...]
                        Name of board to unlock per boards_config.json
  --unlock-all          Unlock all resources in lock directory
  -l [LOCK ...], --lock [LOCK ...]
                        Name of board to lock per boards_config.json
  --owner OWNER         Name of user locking or unlocking
  --list-usage          Display basic usage stats of the boardsincluding if they are locked and when they were locked
  -g GET_VALUE, --get-value GET_VALUE
                        Get value for resource in config (ex: max32655_board1.dap_sn)
  -go GET_OWNER, --get-owner GET_OWNER
                        Get owner of resource if locked
```

### Locking

- Boards can be locked using the ``-l`` or ``--lock`` option. Example: ``resource_manager.py -l board1 board2``
- If wanted, ownership can optionally be applied using the ``--owner`` flag. Example: ``resource_manager.py -l board1 --owner Eve``. The owner will be stored along with the lock information.  

### Unlocking

- Boards can be locked using the ``-u`` or ``--unlock`` option. Example: ``resource_manager.py -u board1 board2``
- If locked with an owner, the owner is required to unlock the board. Example: ``resource_manager.py -u board1 --owner Eve``
- The --unlock-all flag is a master unlock and requires no ownership. It should only be used at the command line directly and manually if a deadlock should occur, or resources were not properly cleaned up.

### Querying usage

- Any value of the board config can be queried using the ``-g`` flag
- If your query does not resolve to a single value you will get a printout of the the json

Input

```bash
resource_manager -g max32655_board2.ocdport.gdb
```

Output

```bash
3552
```

### Usage

The ``--list-usage`` flag can be used to print the a usage table

```bash
╒════════════════════════╤══════════╤═════════╤═════════════════════╤═════════╕
│ NAME                   │ IN-USE   │ GROUP   │ START               │ OWNER   │
╞════════════════════════╪══════════╪═════════╪═════════════════════╪═════════╡
│ max32570_board0        │ False    │         │                     │         │
├────────────────────────┼──────────┼─────────┼─────────────────────┼─────────┤
│ max32655_e2            │ False    │ APP     │                     │         │
├────────────────────────┼──────────┼─────────┼─────────────────────┼─────────┤
│ max32665_1             │ False    │ APP     │                     │         │
├────────────────────────┼──────────┼─────────┼─────────────────────┼─────────┤
│ max32690_1             │ True     │ APP     │ 25/04/2024 10:37:46 │   Eve   │
╘════════════════════════╧══════════╧═════════╧═════════════════════╧═════════╛
```

The usage table lists the following:

- Name: Resource Name
- In-Use: If the board is currently locked
- Group: (APP/RFPHY/OTHER)
- Start: When the board was locked
- Owner: Who owns the board (Empty if no ownership was applied)

## OpenOCD Utils

Along with the Resource manager CLI, there are a few cli tools installed as well which help with flashing, erasing, reseting and debugging ad MAX32 target.

- ocdreset : reset target
- ocderase : erase target flash
- ocdflash : flash target with program
- ocdopen : open an ocd session to connect to via GDB

## Minimal Resource Manager Setup for Local Use

### Install the resource manager

Linux:

```bash
cd Resource_Share
chmod +x install.sh
./install.sh
```

Windows:

```cmd
cd Resource_Share
install.bat
```

As this is a python library you must have python 3.8 or higher installed to use it.

Verify the installation by running ``resource_manager -v`` in the terminal

### Create a Locks Directory

Linux:

```bash
mdkir ~/resource_locks

```

Windows:

```bash
mkdir C:\resource_locks
```

### Create a Config Directory and board_config.json

Linux:

```bash
mdkir ~/resource_configs
cd ~/resource_configs
touch board_config.json
```

Windows:

```bash
mkdir C:\resource_configs
cd resource_configs
copy /b board_config.json +,,
```

Inside ``board_config.json``, create an entry like the one shown in  [Board Config](#board-config)

### Set environment variables to point to files

Replace MAXIM_PATH with the location of your MaximSDK installation.
If you have a place where OpenOCD is then use that instead.
Linux:

```bash
echo export OPENOCD_PATH="~/<MAXIM_PATH>/Tools/OpenOCD/scripts" >> ~/.bashrc
echo export CI_BOARD_CONFIG="~/resource_configs/board_config.json" >> ~/.bashrc
echo export RESOURCE_LOCK_DIR="~/resource_locks" >> ~/.bashrc
```

Windows:

```powershell
setx OPENOCD_PATH "C:\<MAXIM_PATH>\Tool\OpenOCD\scripts"
setx CI_BOARD_CONFIG "C:\resource_configs\board_config.json"
setx RESOURCE_LOCK_DIR "C:\resource_locks"
```

Start a new terminal and test your configuration by typing ``resource_manager -lu``. You should see an output similar to [this](#usage)

### Verify your board config

Run ``ocdreset <resource-name>`` on a board you entered into the board_config.json
