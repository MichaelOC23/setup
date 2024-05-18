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
ensure_process_stopped_by_name "MyTechFlaskBackground"
ensure_process_stopped_by_name "python"
# # ensure_process_stopped_by_name "Docker"
# # ensure_process_stopped_by_name "docker"
# ensure_process_stopped_by_name "chainlit"
# ensure_process_stopped_by_name "ollama"
