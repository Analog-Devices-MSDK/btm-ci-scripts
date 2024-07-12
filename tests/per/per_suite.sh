
export MAXIM_PATH=~/Workspace/msdk
export RF_PATH=~/Workspace/msdk/Libraries/RF-PHY-closed
CENTRAL=me18-1
PERIPHERAL=me17-2


# stability     
python3 connnection_stability.py $CENTRAL $PERIPHERAL 
