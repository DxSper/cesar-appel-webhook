#!/bin/bash
# Start the César attendance bot in continuous mode (systemd)
# Assurez-vous d'avoir configuré le fichier .env avant de lancer

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the bot in continuous mode
python3 bot.py --webhook "$DISCORD_WEBHOOK_URL" --continuous
