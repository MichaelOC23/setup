#!/bin/bash
# ENV_VARIABLES.sh

dcli sync 

export ENV_VAR_LOAD_DATE_TIME=$(date '+%Y-%m-%d %H:%M:%S')

json_string=$(dcli note localeFormat=UNIVERSAL -o json)
#echo $json_string

# Loop through each entry in the JSON array
echo $json_string | jq -c '.[]' | while read -r i; do
    # Extract title and content
    title=$(echo $i | jq -r '.title')
    content=$(echo $i | jq -r '.content')

    # Export them as environment variables
    export "$title=$content"
    #echo "Exported $title=$content"
done

echo "Environment Variables Updated: $ENV_VAR_LOAD_DATE_TIME"