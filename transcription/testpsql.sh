#!/bin/bash

# Database connection details
DB_HOST="michael.ch6qakwu269h.us-east-1.rds.amazonaws.com"
DB_NAME="postgres"
DB_PORT=5432
DB_USER="postgres"
DB_PASSWORD=${POSTGRES_JBI_PASSWORD}
DB_CONN_STRING="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

TRANS_FOLDER_PATH="/Users/michasmi/code/MyTech/transcriptions/testtrans" #Test
# psql $DB_CONN_STRING -c "INSERT INTO TranscriptionLog (filename) VALUES ('testvalue');"
TESTVAL="testvalue"

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -t -c "SELECT EXISTS (SELECT 1 FROM TranscriptionLog WHERE filename = '${TESTVAL}');" | tr -d ' '

exit 0

psql "host=$DB_HOST dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD" -c "INSERT INTO TranscriptionLog (filename) VALUES ('$file_name_only');"

exit 0

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -t -c "SELECT EXISTS (SELECT 1 FROM TranscriptionLog WHERE filename = '$FILE_NAME_ONLY');" | tr -d ' '

# Function to check if a file is already processed
is_file_processed() {
    local file_name_only=$1
    echo -e "Checking if $file_name_only is already processed: "
    # psql "host=$DB_HOST:$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD" -t -c "SELECT EXISTS (SELECT 1 FROM TranscriptionLog WHERE filename = '$file_name_only');" | tr -d ' '

}

# Function to mark a file as processed
mark_file_processed() {
    local file_name_only=$1
    echo -e "Marking $file_name_only as processed."
    psql "host=$DB_HOST dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD" -c "INSERT INTO TranscriptionLog (filename) VALUES ('$file_name_only');"
}

# Function to insert transcription into TextLibrary
insert_transcription_into_db() {
    local file_name_only=$1
    local transcription_path=$2
    local alltext=$(jq -r '.results.channels[0].alternatives[0].transcript' "$transcription_path")
    local structdata=$(jq -c '.' "$transcription_path")
    local _bypage=$(jq -c '.results.channels[0].alternatives[0].paragraphs.paragraphs[0].sentences' "$transcription_path")

    echo -e "Inserting transcription for $file_name_only into database."

    psql "host=$DB_HOST dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD" <<EOF
    INSERT INTO TextLibrary (filename, alltext, structdata, _bypage)
    VALUES ('$file_name_only', \$\$${alltext}\$\$, '$structdata', '$_bypage');
EOF
}

# Echo all the paths
echo "Folder Path: $FOLDER_PATH"
echo "Transcription Folder Path: $TRANS_FOLDER_PATH"

# Function to process m4a files
process_m4a_files() {
    for file in "$FOLDER_PATH"/*.m4a; do
        echo -e "\033[1;95mProcessing file: $file\033[0m"
        base_name="${file%.m4a}"
        file_name_only=$(basename "$base_name")

        if [[ $(is_file_processed "$file_name_only") == "t" ]]; then
            echo -e "\033[1;36mSkipping conversion for ${file_name_only}, already processed.\033[0m"
            continue
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
        base_name="${mp3_file%.mp3}"
        file_name_only=$(basename "$base_name")
        transcription_path="${TRANS_FOLDER_PATH}/${file_name_only}.json"

        if [[ ! -f "$transcription_path" ]]; then
            echo -e "\033[1;95mBeginning transcription of ${file_name_only}.mp3\033[0m"
            curl -X POST \
                -H "Authorization: Token $AUTH_TOKEN" \
                --header 'Content-Type: audio/wav' \
                --data-binary @"$mp3_file" \
                "$DEEPGRAM_URL" >"$transcription_path"

            if [[ $? -eq 0 ]]; then
                echo -e "\033[0;32mTranscription COMPLETE to ${file_name_only}.json.\033[0m"
                insert_transcription_into_db "$file_name_only" "$transcription_path"
                mark_file_processed "$file_name_only"
            else
                echo -e "\033[0;31mTranscription FAILED for ${file_name_only}.mp3.\033[0m"
            fi
        else
            echo -e "\033[1;36mTranscription file ${file_name_only}.json already exists.\033[0m"
        fi
    done
    echo -e "\\033[0;32mTranscription of mp3 files complete.\033[0m"
}

# Process m4a files
process_m4a_files

# Transcribe mp3 files
transcribe_mp3_files

wait
