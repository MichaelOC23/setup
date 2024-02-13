#!/bin/bash
# echo $1
# echo $2
# echo $3

ENDPOINT="https://api.openai.com/v1/chat/completions"
HEADERS="Content-Type: application/json"
PROMPT=$1

REQUEST="{\
      \"model\": \"gpt-4-1106-preview\",\
      \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}],\
      \"temperature\": 0.7\
}"

echo $REQUEST
# Send the request to the GPT-3 API
RESPONSE=$(curl -X POST -H "$HEADERS" -H "Authorization: Bearer $OPENAI_API_KEY" -d "$REQUEST" "$ENDPOINT")

# Extract messages.0.content from the response, or an error message
CONTENT=$(echo $RESPONSE | jq -r '.choices[0].message.content // .error.message')

# Print the relevant content
echo "$CONTENT"
