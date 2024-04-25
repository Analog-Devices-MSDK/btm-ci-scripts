# Board Config and Resource Manager

## Board Config
The board config describes all hardware connected to the CI machine. 



Example:
```
"max32655_board_2" : {
    "desc"         : "marked sn #2, for per test,",
    "target"       : "MAX32655",
    "board"        : "EvKit_V1",
    "rev"          : "PCB-00177-B-0",
    "group"        : "APP",
    "dap_sn"       : "04090000ceeb82b000000000000000000000000097969906",
    "console_port" : "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D309ZDEP-if00-port0",
    "hci_port"     : "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DT03OH8D-if00-port0",
    "sw_model"     : "USB-1SP16T-83H",
    "sw_state"     : "1",
    "ocdports"     : {
        "gdb"    : "3552",
        "tcl"    : "4552",
        "telnet" : "6552"
    },
    "dbbfile"      : "max32655_board_2.json"
}
```
### Required Fields if programmable with openocd
- Target : Chip target as found in openocd target
- dap_sn : Serial number of dap programmer
- ocdports : Ports to flash on

### Optional fields
All fields are optional if they do not require the field. For example, a spectrum anaylzer does not need a board field. This can be left null in that case.

### Value usage
Any value can be queried using the resource manager for use in workflows, actions, and test scripts.

## Resource Manager
The resource manager is a global script on walle, which can be used both in other python scripts and from the command line. It's primary functions are
- Lock/Unlcock hardware resources
- Query resource information
- Monitor resources



### CLI usage
```
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

<br>
Input

```
resource_manager.py max32655_board2.ocdport.gdb
```
Output
```
3552
```


### Usage
The ``--list-usage`` flag can be used to print the a usage table
```
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
