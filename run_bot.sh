#!/bin/bash
# Start the César attendance bot in the background
# Assurez-vous d'avoir configuré le fichier .env avant de lancer

# Go to script directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the bot
python3 main.py run \
    --start-hour 9 \
    --start-minute 13 \
    --afternoon-hour 13 \
    --afternoon-minute 43 \
    --schedule-hour 8 \
    --schedule-minute 0 \
    --check-interval 60
