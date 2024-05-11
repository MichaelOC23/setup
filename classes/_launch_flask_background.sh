#!/bin/bash

ensure_process_stopped_by_name() {
    process_name="$1"

    # Get PIDs of processes with names containing the provided pattern
    pids=$(pgrep -f "$process_name")

    if [ -n "$pids" ]; then # If any PIDs were found
        echo -e "\033[1;95m ** ${process_name} processes are running. Killing them:\033[0m **"
        echo "$pids" # Display the PIDs for clarity

        kill -9 $pids                                  # Forcefully kill the processes
        ensure_process_stopped_by_name ${process_name} # Call the function again to ensure the processes were killed
    else
        echo -e "\033[1;92mNo ${process_name} processes found running.\033[0m"
    fi
}

# Call the function to kill processes with 'docker' in their names
ensure_process_stopped_by_name "Python"

# Change to the directory where the code is located
cd /Users/michasmi/.jbi/
echo "Changed to the directory where the code is located."

# Activate the virtual environment and set the FLASK_APP environment variable
source /Users/michasmi/.jbi/jbi_venv/bin/activate
echo "Activated the virtual environment."

# Set the FLASK_APP environment variable (which is the path to the Flask app)
export FLASK_APP=/Users/michasmi/.jbi/classes/_flask_background.py

# Run the Flask app in the background
flask run --port 5005 &
echo "Flask app running in the background."

# Wait before resuming the script
echo "Waiting for 3 seconds to test the app."
sleep 3 # Pause for 5 seconds
curl http://127.0.0.1:5005/isup
