#!/bin/bash
# Start the César attendance bot in daemon mode
# Assurez-vous d'avoir configuré le fichier .env avant de lancer

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the bot in daemon mode
python3 main.py run \
    --start-hour 9 \
    --start-minute 13 \
    --afternoon-hour 13 \
    --afternoon-minute 43 \
    --schedule-hour 8 \
    --schedule-minute 0 \
    --check-interval 60
