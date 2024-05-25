#!/bin/bash

# Define the folder containing the files as the current working directory
FOLDER_PATH=$(pwd)
AUTH_TOKEN=${DEEPGRAM_API_KEY}
BIT_RATE="64k"
DEEPGRAM_URL="https://api.deepgram.com/v1/listen?topics=true&smart_format=true&punctuate=true&paragraphs=true&keywords=Sales%3A3&keywords=Marketing%3A3&keywords=Product%3A3&keywords=Client%3A3&keywords=Prospect%3A3&diarize=true&sentiment=true&language=en&model=nova-2"

# Loop through all files in the folder
for file in "$FOLDER_PATH"/*; do
    # Check if the file is an m4a file
    if [[ "$file" == *.m4a ]]; then
        # Get the base name of the file without extension
        base_name="${file%.m4a}"
        file_name_only=$(basename "$base_name")
        # Check if the mp3 file already exists
        if [[ -f "${base_name}.mp3" ]]; then
            echo -e "S\033[1;36mkipping conversion for ${file_name_only}, mp3 already exists.\033[0m"
            continue
        fi
        # Convert the m4a file to mp3 using ffmpeg
        echo -e "\033[1;95mBeginning conversion of ${file_name_only}.m4a to mp3.\033[0m"
        ffmpeg -i "$file" -b:a $BIT_RATE "${base_name}.mp3" &
        echo -e "\033[0;32mConversion COMPLETE to ${file_name_only}.mp3.\033[0m"
    fi
done
wait

# Loop through all files again to process mp3 files without a corresponding json file
for mp3_file in "$FOLDER_PATH"/*.mp3; do
    # Get the base name of the mp3 file without extension
    base_name="${mp3_file%.mp3}"
    file_name_only=$(basename "$base_name")
    # Check if the corresponding json file does not exist
    if [[ ! -f "${base_name}.json" ]]; then
        echo -e "\033[1;95mBeginning transcription of ${file_name_only}.mp3\033[0m"
        # Run the curl command to process the mp3 file with Deepgram API
        curl -X POST \
            -H "Authorization: Token $AUTH_TOKEN" \
            --header 'Content-Type: audio/wav' \
            --data-binary @"$mp3_file" \
            "$DEEPGRAM_URL" >"${base_name}.json" &
        echo -e "\033[0;32mTranscription COMPLETE to ${file_name_only}.json.\033[0m"
    else
        echo -e "\033[1;36mTranscription file ${file_name_only}.json already exists.\033[0m"

    fi
done
wait
