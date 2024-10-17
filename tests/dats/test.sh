CLIENT="me17-2"
SERVER="me17-1"

EXAMPLES_DIR=~/Workspace/msdk/Examples/MAX32655/Bluetooth
DATS_DIR=$EXAMPLES_DIR/BLE_dats
DATC_DIR=$EXAMPLES_DIR/BLE_datc

make -C $DATS_DIR && make -C $DATC_DIR
cp $DATS_DIR/build/max32655.elf bin/dats_655.elf
cp $DATC_DIR/build/max32655.elf bin/datc_655.elf


ocderase $SERVER && ocderase $CLIENT

ocdflash $SERVER bin/dats_655.elf
ocdflash $CLIENT bin/datc_655.elf

python3 datsc_connected.py $SERVER $CLIENT
