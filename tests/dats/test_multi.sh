

# Initialize counter
success_count=0

# Loop to run the script 10 times
for i in {1..10}; do
    echo "Running iteration $i"
    
    # Run your script or command
    ./test.sh
    
    # Check if the script was successful (exit status 0)
    if [ $? -eq 0 ]; then
        # Increment the counter for success
        success_count=$((success_count + 1))
    else
        mv dats_out "dats_out_failure$i"
    fi
done


printf "Total Passes %d" $success_count
