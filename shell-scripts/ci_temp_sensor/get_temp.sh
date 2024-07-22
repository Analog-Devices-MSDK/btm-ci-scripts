#! /usr/bin/bash

<<"CONFIGURATION"
using the MAX32690EVKIT:
-   Connect a USB cable between the PC and the CN2 (USB/PWR) connector.
-   Install JP7(RX_EN) and JP8(TX_EN) headers.
-   Open a terminal application on the PC and connect to the EV kit's console UART at 115200, 8-N-1.
-   Close jumper JP5 (LED1 EN).
-   Close jumper JP6 (LED2 EN).
-   You must connect P2.8 (SCL), P2.7 (SDA), VDD and GND to corresponding pins of MAX31889 EVKIT_A board (via J3 terminal).
CONFIGURATION


# variable for configuration
baudRate=115200
timeLimit=1
boardVersion=max32690
temp_path=$(dirname "$0")


boardName=$1
uartPort=$(resource_manager -g $boardName.console_port)
target_uc=$(resource_manager -g $boardName.target)
tempFile=$temp_path/.temperature.txt

#make -C $temp_path distclean > /dev/null

#make -C $temp_path -j > /dev/null

stty -F $uartPort $baudRate > /dev/null
#ocdflash $boardName $temp_path/build/$boardVersion.elf > /dev/null 2>&1

timeout $timeLimit cat $uartPort > $tempFile

head -1 $tempFile

rm -rf $tempFile
