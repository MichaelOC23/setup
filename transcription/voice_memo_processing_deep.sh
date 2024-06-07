#!/bin/bash

# Define the folder containing the files as the current working directory

FOLDER_PATH="/Users/michasmi/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
TRANS_FOLDER_PATH="/Users/michasmi/code/MyTech/transcriptions"
SKIP_LIST_FILE="${PWD}/skiplist.txt"
AUTH_TOKEN=${DEEPGRAM_API_KEY}
BIT_RATE="64k"
DEEPGRAM_URL="https://api.deepgram.com/v1/listen?topics=true&smart_format=true&punctuate=true&paragraphs=true&keywords=Sales%3A3&keywords=Marketing%3A3&keywords=Product%3A3&keywords=Client%3A3&keywords=Prospect%3A3&diarize=true&sentiment=true&language=en&model=nova-2"

# Echo all the paths and file paths
echo "Folder Path: $FOLDER_PATH"
echo "Transcription Folder Path: $TRANS_FOLDER_PATH"
echo "Skip List File: $SKIP_LIST_FILE"


# Define the skip list file


# Check if the skip list file exists
if [[ ! -f "$SKIP_LIST_FILE" ]]; then
    echo "Skip list file not found at $SKIP_LIST_FILE. Creating an empty one."
    touch "$SKIP_LIST_FILE"
fi

# Loop through all files in the folder
for file in "$FOLDER_PATH"/*; do
    echo -e "\033[1;95mProcessing file: $file\033[0m"
    # Check if the file is an m4a file
    if [[ "$file" == *.m4a ]]; then
        # Get the base name of the file without extension
        base_name="${file%.m4a}" &
        file_name_only=$(basename "$base_name")

        # Check if the base name is in the skip list file
        if grep -q "^${file_name_only}$" "$SKIP_LIST_FILE"; then
            echo -e "\033[1;36mSkipping conversion for ${file_name_only}, listed in skip list.\033[0m"
            continue
        fi

        # Convert the m4a file to mp3 using ffmpeg
        echo -e "\033[1;95mBeginning conversion of ${file_name_only}.m4a to mp3.\033[0m"
        ffmpeg -y -i "$file" -b:a $BIT_RATE "${base_name}.mp3"
        if [[ $? -eq 0 ]]; then
            echo -e "\033[0;32mConversion COMPLETE to ${file_name_only}.mp3.\033[0m"
        else
            echo -e "\033[0;31mConversion FAILED for ${file_name_only}.m4a.\033[0m"
        fi
    fi
done
wait

# Loop through all files again to process mp3 files without a corresponding json file
for mp3_file in "$FOLDER_PATH"/*.mp3; do
    # Get the base name of the mp3 file without extension
    base_name="${mp3_file%.mp3}"
    file_name_only=$(basename "$base_name")

    # Define the path for the transcription JSON file
    transcription_path="${TRANS_FOLDER_PATH}/${file_name_only}.json"

    # Check if the corresponding json file does not exist in the Transcriptions folder
    if [[ ! -f "$transcription_path" ]]; then
        echo -e "\033[1;95mBeginning transcription of ${file_name_only}.mp3\033[0m"
        # Run the curl command to process the mp3 file with Deepgram API
        curl -X POST \
            -H "Authorization: Token $AUTH_TOKEN" \
            --header 'Content-Type: audio/wav' \
            --data-binary @"$mp3_file" \
            "$DEEPGRAM_URL" >"$transcription_path" &
            sleep 3
        echo -e "\033[0;32mTranscription COMPLETE to ${file_name_only}.json.\033[0m"
        echo "$file_name_only" >>"$SKIP_LIST_FILE"
    else
        echo -e "\033[1;36mTranscription file ${file_name_only}.json already exists.\033[0m"
    fi
done
wait
