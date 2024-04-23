#!/bin/bash

BOARD_SERVER="${{ inputs.board_server }}"
BOARD_CLIENT="${{ inputs.board_client }}"

target_server=$(resource_manager.py -g ${BOARD_SERVER}.target)
target_client=$(resource_manager.py -g ${BOARD_CLIENT}.target)
target_server_lower=$(lower ${target_server})
target_client_lower=$(lower ${target_client})

msdk_path="${{ inputs.msdk_path }}"
elf_server=${msdk_path}/Examples/${target_server}/Bluetooth/BLE_otas/build/${target_server_lower}.elf
elf_client=${msdk_path}/Examples/${target_client}/Bluetooth/BLE_otas/build/${target_client_lower}.elf


cd ../../../tests/ && datsc_connected.py $target_server $target_client $elf_server $elf_client
