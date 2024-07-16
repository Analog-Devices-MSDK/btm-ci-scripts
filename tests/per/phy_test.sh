
export MAXIM_PATH=~/Workspace/msdk
export RF_PATH=~/Workspace/msdk/Libraries/RF-PHY-closed

TESTER=me18-1
DUT=me17-2


# DTM
python3 per_heatmap.py $DUT $TESTER

# Non Connected
python3 advertise.py $DUT
python3 scan.py $DUT

# Connection      
python3 per_connection.py $TESTER $DUT
python3 connnection_stability.py $TESTER $DUT 
