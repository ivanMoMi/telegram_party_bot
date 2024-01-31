#!/bin/bash
API_KEY="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"
MODEL_NAME="gpt-3.5-turbo"
CONTEXT='{"role": "system", "content": "You are a helpful assistant."}'
MESSAGES=""
GREEN="\033[32m"
RESET="\033[0m"
PREGUNTA_PROMPT="Buenas, soy ChatGPT, necesitas algo? Pregunta:"

prompt_user() {
    echo -e "$GREEN $PREGUNTA_PROMPT $RESET"
    read -p $'\n ' content
    PREGUNTA_PROMPT="\nTienes mas dudas? Adelante, pregunta:"
    echo -e "$RESET"
}

while true; do
    prompt_user
  # Eliminar lC-neas en blanco y agregar el nuevo mensaje al string
    new_message=$(echo ",{\"role\": \"user\", \"content\": \"$content\"}" | awk 'NF' | tr -d '\n')
    MESSAGES="$MESSAGES$new_message"

    # Realizar la solicitud a la API de ChatGPT
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{\"model\": \"$MODEL_NAME\", \"messages\": [ $CONTEXT $MESSAGES  ]}" \
        "https://api.openai.com/v1/chat/completions")
echo $RESPONSE
    # Extraer la parte del campo "content" utilizando awk
    CONTENIDO=$(echo "$RESPONSE" | awk -F'"content": ' '{gsub(/[{}]/, "", $2); print $2 }' | sed 's/\\\(\"\)/\1/g')

    # Imprimir el contenido formateado
    CONTENIDO_LIMPIO=$(echo "$CONTENIDO" | awk 'NF' | awk '{$1=$1};1' | awk '{gsub (/^\"|\"$/,""); gsub(/```bash/,"\033[92m");gsub(/```python/,"\033[33m");  gsub (/```/,"\033[0m"); print}')
    echo -e "${GREEN}ChatGPT: ${RESET}$CONTENIDO_LIMPIO"
    done
