source ~/Tools/btm-ci-scripts/str-utils.sh
function ocdflash() {
    if [[ "$1" == "--help" || $1 == "-h" ]]; then
        printf "flash --> flash a board\n"
        printf "=======================\n"
        printf "usage: flash BOARDNAME ELFFILE\n"
        printf "\tBOARDNAME => board to flash, names defined in boards_config.json.\n"
        printf "\tELFFILE   => path to the elf file to flash onto board.\n"
        return 0
    fi
    if [[ $# -ne 2 ]]; then
        echo "Improper use! Expected: 2 arguments, Received: $#" 
    fi
    name=$1
    elfFile=$2

    target=$(resource_manager.py -g $name.target)
    dapsn=$(resource_manager.py -g $name.dap_sn)
    gdbport=$(resource_manager.py -g $name.ocdports.gdb)
    telnetport=$(resource_manager.py -g $name.ocdports.telnet)
    tclport=$(resource_manager.py -g $name.ocdports.tcl)

    openocd -s $OPENOCD_PATH/tcl \
    -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
    -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
    -c "program $elfFile verify; reset; exit"

    if [[ $? -ne 0 ]]; then
        openocd -s $OPENOCD_PATH/tcl \
        -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
        -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
        -c "program $elfFile verify; reset; exit"
    fi

    return $?

}

function ocderase() {
    if [[ "$1" == "--help" || $1 == "-h" ]]; then
        printf "erase --> mass-erase flash\n"
        printf "==========================\n"
        printf "usage: erase BOARDNAME\n"
        printf "\tBOARDNAME => board to erase, names defined in boards_config.json.\n"
        return 0
    fi
    if [[ $# -ne 1 ]]; then
        echo "Improper use! Expected: 1 argument, Received: $#"
    fi

    name=$1

    target=$(resource_manager.py -g $name.target)
    dapsn=$(resource_manager.py -g $name.dap_sn)
    gdbport=$(resource_manager.py -g $name.ocdports.gdb)
    telnetport=$(resource_manager.py -g $name.ocdports.telnet)
    tclport=$(resource_manager.py -g $name.ocdports.tcl)

    openocd -s $OPENOCD_PATH/tcl \
    -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
    -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
    -c "init; reset halt; max32xxx mass_erase 0;" -c exit
    if [[ "$target" == "MAX32655" ]]; then
        return $?
    fi
    openocd -s $OPENOCD_PATH/tcl \
        -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
        -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
        -c "init; reset halt; max32xxx mass_erase 1;" -c exit

    return $?

}
