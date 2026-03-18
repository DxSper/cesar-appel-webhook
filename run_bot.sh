#!/bin/bash
# Start the César attendance bot in the background
# Assurez-vous d'avoir configuré le fichier .env avant de lancer

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the bot
python3 bot.py \
    --webhook "$DISCORD_WEBHOOK_URL" \
    --start-hour 9 \
    --start-minute 13 \
    --afternoon-hour 13 \
    --afternoon-minute 43 \
    --check-interval 60
