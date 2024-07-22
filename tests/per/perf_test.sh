#!/usr/bin/env bash

# CONFIG
export MAXIM_PATH=~/Workspace/msdk
export RF_PATH=~/Workspace/msdk/Libraries/RF-PHY-closed

TESTER=me18-1
DUT=me17-2
DATE=$(printf '%(%Y-%m-%d)T\n' -1)

DO_DTM=1
DO_NON_CONNECTED=1
DO_CONNECTED=1


# Build and Flash

TESTER_TARGET=$(resource_manager -g ${TESTER}.target)
DUT_TARGET=$(resource_manager -g ${DUT}.target)

make -C $RF_PATH/"$TESTER_TARGET"/build/gcc -j
make -C $RF_PATH/"$DUT_TARGET"/build/gcc -j

DUT_EXAMPLE=$MAXIM_PATH/Examples/"$DUT_TARGET"/Bluetooth/BLE5_ctr
TESTER_EXAMPLE=$MAXIM_PATH/Examples/"$TESTER_TARGET"/Bluetooth/BLE5_ctr

make -C "$DUT_EXAMPLE" -j
make -C "$TESTER_EXAMPLE" -j

(cd "$DUT_EXAMPLE" && ocdflash $DUT)
(cd "$TESTER_EXAMPLE" && ocdflash $TESTER)

echo TESTER $TESTER
echo DUT $DUT

# DTM
if [[ $DO_DTM -ne 0 ]]; then
if [[ $USER == "btm-ci" ]]; then

    CHANNELS=0,19,39
    NUM_PACKETS=1000
    NUM_PACKETS_CODED=100
    HEATMAP_RESULTS=heatmap-results-$DATE

    python3 per_heatmap.py $TESTER $DUT --phy 1M --channels $CHANNELS --results "$HEATMAP_RESULTS/per_1m" --num-packets $NUM_PACKETS
    python3 per_heatmap.py $TESTER $DUT --phy 2M --channels $CHANNELS --results "$HEATMAP_RESULTS/per_2m" --num-packets $NUM_PACKETS
    python3 per_heatmap.py $TESTER $DUT --phy S2 --channels $CHANNELS --results "$HEATMAP_RESULTS/per_s2" --num_packets $NUM_PACKETS_CODED
    python3 per_heatmap.py $TESTER $DUT --phy S8 --channels $CHANNELS --results "$HEATMAP_RESULTS/per_s8" --num_packets $NUM_PACKETS_CODED

else
    CHANNEL=19
    PACKET_LEN=100
    DTM_TIME=30
    mkdir -p dtm_out    
    python3 simple_dtm.py $TESTER $DUT -c $CHANNEL -pl $PACKET_LEN -t $DTM_TIME --phy 1M | tee dtm_out/dtm_1m.out 
    python3 simple_dtm.py $TESTER $DUT -c $CHANNEL -pl $PACKET_LEN -t $DTM_TIME --phy 2M | tee dtm_out/dtm_2m.out
    python3 simple_dtm.py $TESTER $DUT -c $CHANNEL -pl $PACKET_LEN -t $DTM_TIME --phy S2 | tee dtm_out/dtm_s2.out
    python3 simple_dtm.py $TESTER $DUT -c $CHANNEL -pl $PACKET_LEN -t $DTM_TIME --phy S8 | tee dtm_out/dtm_s8.out

fi
ocdreset $DUT
ocdreset $TESTER
fi

# Non connected
if [[ $DO_NON_CONNECTED -ne 0 ]]; then
ADV_SAMPLE_RATE=1
ADV_TEST_TIME_SEC=1800
ADV_RESULTS=advertise-results-$DATE
python3 advertise_perf.py $DUT -t $ADV_TEST_TIME_SEC -s $ADV_SAMPLE_RATE -d "$ADV_RESULTS"

SCAN_SAMPLE_RATE=1
SCAN_TEST_TIME_SEC=1800
SCAN_RESULTS=advertise-results-$DATE
python3 scan_perf.py $DUT -t $SCAN_TEST_TIME_SEC -s $SCAN_SAMPLE_RATE -d "$SCAN_RESULTS"

ocdreset $DUT
ocdreset $TESTER

fi

# Connection

if [[ $DO_CONNECTED -ne 0 ]]; then

PER_CONN_HOLD_TIME=10
PER_CONN_ATTENS=-20:-2:-100
PER_CONN_RESULTS=per-conn-$DATE

python3 per_connection.py $TESTER $DUT -p 1M -d "$PER_CONN_RESULTS" -t $PER_CONN_HOLD_TIME -a $PER_CONN_ATTENS
python3 per_connection.py $TESTER $DUT -p 2M -d "$PER_CONN_RESULTS" -t $PER_CONN_HOLD_TIME -a $PER_CONN_ATTENS
python3 per_connection.py $TESTER $DUT -p S2 -d "$PER_CONN_RESULTS" -t $PER_CONN_HOLD_TIME -a $PER_CONN_ATTENS
python3 per_connection.py $TESTER $DUT -p S8 -d "$PER_CONN_RESULTS" -t $PER_CONN_HOLD_TIME -a $PER_CONN_ATTENS

CONN_STAB_SAMPLE_RATE_SEC=1
CONN_TEST_TIME_SEC=1800
CONN_STAB_RESULTS=conn-stability-$DATE

python3 connnection_stability.py $TESTER $DUT -p 1M -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d "$CONN_STAB_RESULTS"
python3 connnection_stability.py $TESTER $DUT -p 2M -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d "$CONN_STAB_RESULTS"
python3 connnection_stability.py $TESTER $DUT -p S2 -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d "$CONN_STAB_RESULTS"
python3 connnection_stability.py $TESTER $DUT -p S8 -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d "$CONN_STAB_RESULTS"

ocdreset $DUT
ocdreset $TESTER

fi
