#!/usr/bin/env bash

export MAXIM_PATH=~/Workspace/msdk
export RF_PATH=~/Workspace/msdk/Libraries/RF-PHY-closed

TESTER=me18-1
DUT=me17-2

DATE=$(printf '%(%Y-%m-%d)T\n' -1)

# DTM
CHANNELS=0,19,39
NUM_PACKETS=1000
NUM_PACKETS_CODED=100
HEATMAP_RESULTS=heatmap-results-$DATE


python3 per_heatmap.py $TESTER $DUT --phy 1M --channels $CHANNELS --results "$HEATMAP_RESULTS/per_1m" --num-packets $NUM_PACKETS
python3 per_heatmap.py $TESTER $DUT --phy 2M --channels $CHANNELS --results "$HEATMAP_RESULTS/per_2m" --num-packets $NUM_PACKETS
python3 per_heatmap.py $TESTER $DUT --phy S2 --channels $CHANNELS --results "$HEATMAP_RESULTS/per_s2" --num_packets $NUM_PACKETS_CODED
python3 per_heatmap.py $TESTER $DUT --phy S8 --channels $CHANNELS --results "$HEATMAP_RESULTS/per_s8" --num_packets $NUM_PACKETS_CODED


# Non connected
ADV_SAMPLE_RATE=1
ADV_TEST_TIME_SEC=1800 
ADV_RESULTS=advertise-results-$DATE
python3 advertise.py $DUT -t $ADV_TEST_TIME_SEC -s $ADV_SAMPLE_RATE -d "$ADVERTISE_RESULTS"


SCAN_SAMPLE_RATE=1
SCAN_TEST_TIME_SEC=1800 
SCAN_RESULTS=advertise-results-$DATE
python3 scan.py $DUT -t $SCAN_TEST_TIME_SEC -s $SCAN_SAMPLE_RATE -d "$SCAN_RESULTS"


# Connection      
PER_CONN_SAMPLE_RATE_SEC=1
PER_CONN_TEST_TIME_SEC=1800
PER_CONN_RESULTS=per-conn-$DATE

python3 per_connection.py $TESTER $DUT

CONN_STAB_SAMPLE_RATE_SEC=1
CONN_TEST_TIME_SEC=1800
CONN_STAB_RESULTS=conn-stability-$DATE

python3 connnection_stability.py $TESTER $DUT -p 1M -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d $CONN_STAB_RESULTS
python3 connnection_stability.py $TESTER $DUT -p 2M -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d $CONN_STAB_RESULTS
python3 connnection_stability.py $TESTER $DUT -p S2 -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d $CONN_STAB_RESULTS
python3 connnection_stability.py $TESTER $DUT -p S8 -t $CONN_TEST_TIME_SEC -s $CONN_STAB_SAMPLE_RATE_SEC -d $CONN_STAB_RESULTS
