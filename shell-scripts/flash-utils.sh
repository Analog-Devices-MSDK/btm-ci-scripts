#! /usr/bin/bash

function lower() {
    val=$1
    echo ${val,,}
}

function upper() {
    val=$1
    echo ${val^^}
}

function ocdflash() {
    if [[ "$1" == "--help" || $1 == "-h" ]]; then
        printf "flash --> flash a board\n"
        printf "=======================\n"
        printf "usage: flash BOARDNAME ELFFILE\n"
        printf "\tBOARDNAME => board to flash, names defined in boards_config.json.\n"
        printf "\tELFFILE   => path to the elf file to flash onto board.\n"
        printf "\tOwner   => Optional name of owner who created lockfile.\n"

        return 0
    fi
    # Need at least the name of thre resource 
    if [[ $# -lt 2 ]]; then
        echo "OCDFLASH: Improper use! Expected: 2 arguments, Received: $#" 
        return -1
    fi
    name=$1
    elfFile=$2
    owner=$3
    current_owner=$(resource_manager --get-owner $name)

    if [[ -n $current_owner && $owner != $current_owner ]]; then
        echo Owner $owner does not match current owner $current_owner
        echo Refusing to flash!
        return -1
    fi

    target=$(resource_manager -g $name.target)
    

    
    dapsn=$(resource_manager -g $name.dap_sn)
    gdbport=$(resource_manager -g $name.ocdports.gdb)
    telnetport=$(resource_manager -g $name.ocdports.telnet)
    tclport=$(resource_manager -g $name.ocdports.tcl)

    openocd -s $OPENOCD_PATH \
    -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
    -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
    -c "program $elfFile verify; reset; exit"

    if [[ $? -ne 0 ]]; then
        openocd -s $OPENOCD_PATH \
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
        printf "\tOwner   => Optional name of owner who created lockfile.\n"
        return 0
    fi
    if [[ $# -lt 1 ]]; then
        echo "OCDERASE: Improper use! Expected: 1 argument, Received: $#"
        return -1
    fi

    name=$1
    owner=$2
    current_owner=$(resource_manager --get-owner $name)

    if [[ -n $current_owner && $owner != $current_owner ]]; then
        echo Owner $owner does not match current owner $current_owner
        echo Refusing to erase!
        return -1
    fi


    target=$(resource_manager -g $name.target)
    
    

    dapsn=$(resource_manager -g $name.dap_sn)
    gdbport=$(resource_manager -g $name.ocdports.gdb)
    telnetport=$(resource_manager -g $name.ocdports.telnet)
    tclport=$(resource_manager -g $name.ocdports.tcl)

   
    openocd -s $OPENOCD_PATH \
    -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
    -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
    -c "init; reset halt; max32xxx mass_erase 0;" -c exit
    if [[ "$target" == "MAX32655" ]]; then
        return $?
    fi
    openocd -s $OPENOCD_PATH \
        -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
        -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
        -c "init; reset halt; max32xxx mass_erase 1;" -c exit

    return $?

}

function ocdreset() {
    if [[ "$1" == "--help" || $1 == "-h" ]]; then
        printf "reset\n"
        printf "==========================\n"
        printf "usage: erase BOARDNAME\n"
        printf "\tBOARDNAME => board to reset, names defined in boards_config.json.\n"
        printf "\tOwner   => Optional name of owner who created lockfile.\n"
        return 0
    fi
    if [[ $# -lt 1 ]]; then
        echo "OCDRESET: Improper use! Expected: 1 argument, Received: $#"
        return -1
    fi

    name=$1
    owner=$2
    current_owner=$(resource_manager --get-owner $name)

    if [[ -n $current_owner && $owner != $current_owner ]]; then
        echo Owner $owner does not match current owner $current_owner
        echo Refusing to reset!
        return -1
    fi

    target=$(resource_manager -g $name.target)

    

    dapsn=$(resource_manager -g $name.dap_sn)
    gdbport=$(resource_manager -g $name.ocdports.gdb)
    telnetport=$(resource_manager -g $name.ocdports.telnet)
    tclport=$(resource_manager -g $name.ocdports.tcl)


    openocd -s $OPENOCD_PATH \
        -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
        -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport" \
        -c "init; reset ;exit" 

    return $?

}
function ocdopen() {
    if [[ "$1" == "--help" || $1 == "-h" ]]; then
        printf "reset\n"
        printf "==========================\n"
        printf "usage: erase BOARDNAME\n"
        printf "\tBOARDNAME => board to reset, names defined in boards_config.json.\n"
        printf "\tOwner   => Optional name of owner who created lockfile.\n"
        return 0
    fi
    if [[ $# -lt 1 ]]; then
        echo "OCDOPEN: Improper use! Expected: at least 1 argument, Received: $#"
        return -1
    fi

    name=$1
    owner=$2
    current_owner=$(resource_manager --get-owner $name)

    if [[ -n $current_owner && $owner != $current_owner ]]; then
        echo Owner $owner does not match current owner $current_owner
        return -1
    fi



    target=$(resource_manager -g $name.target)


    dapsn=$(resource_manager -g $name.dap_sn)
    gdbport=$(resource_manager -g $name.ocdports.gdb)
    telnetport=$(resource_manager -g $name.ocdports.telnet)
    tclport=$(resource_manager -g $name.ocdports.tcl)


    openocd -s $OPENOCD_PATH \
        -f interface/cmsis-dap.cfg -f target/$(lower $target).cfg -c "adapter serial $dapsn" \
        -c "gdb_port $gdbport" -c "telnet_port $telnetport" -c "tcl_port $tclport"

    return $?

}

export -f lower
export -f upper
export -f ocdflash
export -f ocderase
export -f ocdreset
export -f ocdopen
