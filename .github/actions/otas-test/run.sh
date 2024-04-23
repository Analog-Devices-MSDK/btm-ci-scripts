#!/bin/bash

BOARD_SERVER=$1
BOARD_CLIENT=$2

echo "SERVER " $BOARD_SERVER
echo "CLIENT " $BOARD_CLIENT


target_server=$(resource_manager.py -g $BOARD_SERVER.target)
target_client=$(resource_manager.py -g $BOARD_CLIENT.target)
target_server_lower=$(lower ${target_server})
target_client_lower=$(lower ${target_client})

msdk_path=${INPUT_MSDK_PATH}
elf_server=${msdk_path}/Examples/${target_server}/Bluetooth/BLE_otas/build/${target_server_lower}.elf
elf_client=${msdk_path}/Examples/${target_client}/Bluetooth/BLE_otas/build/${target_client_lower}.elf


cd ../../../tests && python3 otas_connected.py $target_server $target_client $elf_server $elf_client
