#!/bin/bash

# Database connection details
DB_HOST="michael.ch6qakwu269h.us-east-1.rds.amazonaws.com"
DB_NAME="postgres"
DB_PORT=5432
DB_USER="postgres"
DB_PASSWORD=${POSTGRES_JBI_PASSWORD}
DB_CONN_STRING="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

# Define the folder containing the files as the current working directory
FOLDER_PATH="/Users/michasmi/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
# FOLDER_PATH="/Users/michasmi/code/MyTech/transcriptions/testaudio" #Test
TRANS_FOLDER_PATH="/Users/michasmi/code/MyTech/transcriptions"
# TRANS_FOLDER_PATH="/Users/michasmi/code/MyTech/transcriptions/testtrans" #Test

AUTH_TOKEN=${DEEPGRAM_API_KEY}
BIT_RATE="64k"
DEEPGRAM_URL="https://api.deepgram.com/v1/listen?topics=true&smart_format=true&punctuate=true&paragraphs=true&keywords=Sales%3A3&keywords=Marketing%3A3&keywords=Product%3A3&keywords=Client%3A3&keywords=Prospect%3A3&diarize=true&sentiment=true&language=en&model=nova-2"

# Echo all the paths
echo "Folder Path: $FOLDER_PATH"
echo "Transcription Folder Path: $TRANS_FOLDER_PATH"

#Check if the DB Password is set in the environment
if [[ -z "$POSTGRES_JBI_PASSWORD" ]]; then
    echo "DB Password is not set. Aborting." >&2
    exit 1
fi

# Check if required commands are available
command -v ffmpeg >/dev/null 2>&1 || {
    echo "ffmpeg is not installed. Aborting." >&2
    exit 1
}
command -v curl >/dev/null 2>&1 || {
    echo "curl is not installed. Aborting." >&2
    exit 1
}
command -v jq >/dev/null 2>&1 || {
    echo "jq is not installed. Aborting." >&2
    exit 1
}

# Function to check if a file is already processed
is_file_processed() {
    local file_name_only=$1
    sqlcommand="SELECT EXISTS (SELECT 1 FROM textlibrary WHERE sourcefilename = '$file_name_only');"
    result=$(psql "$DB_CONN_STRING" -t -c "$sqlcommand" | tr -d '[:space:]')
    echo "$result"
}
# Function to insert transcription into TextLibrary
insert_transcription_into_db() {
    local file_name_only=$1
    local transcription_path=$2
    local alltext=$(jq -r '.results.channels[0].alternatives[0].transcript' "$transcription_path")
    local structdata=$(jq -c '.' "$transcription_path")
    local bypage=$(jq -c '.results.channels[0].alternatives[0].paragraphs.paragraphs[0].sentences' "$transcription_path")

    echo -e "Inserting transcription for $file_name_only into database."

    # Construct the SQL command using concatenation
    local completeSQLcommand="INSERT INTO TextLibrary (sourcefilename, alltext, structdata, bypage) VALUES ("
    completeSQLcommand+="'"${file_name_only}"', "
    completeSQLcommand+="\$\$${alltext}\$\$, "
    completeSQLcommand+="ARRAY[\$\$${structdata}\$\$::jsonb], "
    completeSQLcommand+="ARRAY[\$\$${bypage}\$\$::jsonb]);"

    # Output the SQL command for debugging
    echo -e "SQL Command: $completeSQLcommand"

    # Execute the SQL command
    psql "$DB_CONN_STRING" -c "$completeSQLcommand"
}

# Function to process m4a files
process_m4a_files() {
    for file in "$FOLDER_PATH"/*.m4a; do
        echo -e "\033[1;95mProcessing file: $file\033[0m"
        base_name="${file%.m4a}"
        file_name_only=$(basename "$base_name")

        echo -e "File Name Only: $file_name_only"

                    # Extract title from metadata
        title=$(ffprobe -v error -show_entries format_tags=title -of default=nw=1:nk=1 "$file")
        if [ -z "$title" ]; then
            title="$file_name_only"
        fi

        processed=$(is_file_processed "$file_name_only")
        echo -e "is_file_processed returned: $processed"

        if [[ $processed == "t" ]]; then
            echo -e "\033[1;36mSkipping conversion for ${file_name_only}, already processed.\033[0m"
            continue
        else
            echo -e "\033[1;36mFile ${file_name_only} not processed.\033[0m"
            # Add your processing logic here
        fi

        echo -e "\033[1;95mBeginning conversion of ${file_name_only}.m4a to mp3.\033[0m"
        ffmpeg -y -i "$file" -b:a $BIT_RATE "${base_name}.mp3"
        if [[ $? -eq 0 ]]; then
            echo -e "\033[0;32mConversion COMPLETE to ${file_name_only}.mp3.\033[0m"
        else
            echo -e "\033[0;31mConversion FAILED for ${file_name_only}.m4a.\033[0m"
        fi
    done
    echo -e "\033[0;32mConversion of m4a files complete.\033[0m"
}
# Function to transcribe mp3 files
transcribe_mp3_files() {
    for mp3_file in "$FOLDER_PATH"/*.mp3; do
        {
            base_name="${mp3_file%.mp3}"
            file_name_only=$(basename "$base_name")
            transcription_path="${TRANS_FOLDER_PATH}/${file_name_only}.json"

            echo -e "\033[1;95mProcessing mp3 file: $mp3_file\033[0m"
            echo -e "File Name Only: $file_name_only"
            echo -e "Transcription Path: $transcription_path"

            processed=$(is_file_processed "$file_name_only")
            echo -e "is_file_processed returned: $processed"

            if [[ $processed == "t" ]]; then
                echo -e "\033[1;36mSkipping transcription for ${file_name_only}, already transcribed.\033[0m"
                continue
            fi

            if [[ ! -f "$transcription_path" ]]; then
                echo -e "\033[1;95mBeginning transcription of ${file_name_only}.mp3\033[0m"
                # curl -X POST \
                #     -H "Authorization: Token $AUTH_TOKEN" \
                #     --header 'Content-Type: audio/wav' \
                #     --data-binary @"$mp3_file" \
                #     "$DEEPGRAM_URL" >"$transcription_path"
                # if [[ $? -ne 0 ]]; then
                #     echo -e "\033[0;31mTranscription FAILED for ${file_name_only}.mp3.\033[0m"
                #     continue
                echo -e "\033[5;34m +++ Successfully transcribed to path: $transcription_path +++ \033[0m"
            
            else
                echo -e "\033[1;36mTranscription file ${file_name_only}.json already exists.\033[0m"
            fi

            echo -e "\033[0;32mTranscription COMPLETE to ${file_name_only}.json.\033[0m"
            insert_transcription_into_db "$file_name_only" "$transcription_path"
        } &
    done

    # Wait for all background jobs to complete
    wait
    echo -e "\033[0;32mTranscription of mp3 files complete.\033[0m"
}

# Process m4a files
process_m4a_files

# Transcribe mp3 files
transcribe_mp3_files

wait
