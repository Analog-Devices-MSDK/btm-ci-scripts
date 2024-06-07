export PLATFORM=nordic
MAKE_PATH=$MAXIM_PATH/Libraries/Cordio/controller/build/ble5-ctr/gcc
cd $MAKE_PATH && make install -j SN=$(resource-manager -g nRF52840_1.sn)
