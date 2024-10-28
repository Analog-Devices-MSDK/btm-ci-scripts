CLIENT="me17-1"
SERVER="me17-2"
server_target=$(resource_manager -g $SERVER.target)
client_target=$(resource_manager -g $CLIENT.target)

echo $server_target
echo $client_target



EXAMPLES_DIR_SERVER=~/Workspace/msdk/Examples/${server_target^^}/Bluetooth
EXAMPLES_DIR_CLIENT=~/Workspace/msdk/Examples/${client_target^^}/Bluetooth

DATS_DIR=$EXAMPLES_DIR_SERVER/BLE_dats
DATC_DIR=$EXAMPLES_DIR_CLIENT/BLE_datc

make clean -C "$DATS_DIR" 
make clean -C "$DATC_DIR" 
make -C "$DATS_DIR" ADV_NAME=test
make -C "$DATC_DIR" ADV_NAME=test
cp "$DATS_DIR"/build/"${server_target,,}".elf bin/dats.elf && cp "$DATC_DIR"/build/"${client_target,,}".elf bin/datc.elf

ocderase $SERVER && ocderase $CLIENT
ocdflash $CLIENT bin/datc.elf && ocdflash $SERVER bin/dats.elf

python3 datsc_connected.py $SERVER $CLIENT
