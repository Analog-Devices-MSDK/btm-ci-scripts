function flash() {
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
}

flash board elffile