#!/bin/bash

BOARD_SERVER="${{ inputs.board_server }}"
BOARD_CLIENT="${{ inputs.board_client }}"

target_server=$(resource_manager.py -g ${BOARD_SERVER}.target)
target_client=$(resource_manager.py -g ${BOARD_CLIENT}.target)
target_server_lower=$(lower ${target_server})
target_client_lower=$(lower ${target_client})

msdk_path="${{ inputs.msdk_path }}"
OTAS_PATH=${msdk_path}/Examples/${target_server}/Bluetooth/BLE_otas
OTAC_PATH=${msdk_path}/Examples/${target_server}/Bluetooth/BLE_otac

make -j $OTAS_PATH
make -j $OTAC_PATH


elf_server=$OTAS_PATH/build/${target_server_lower}.elf
elf_client=$OTAC_PATH/build/${target_client_lower}.elf


cd ../../../tests/ && datsc_connected.py $target_server $target_client $elf_server $elf_client
