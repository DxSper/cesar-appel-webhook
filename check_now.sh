#!/bin/bash
# Script pour cron - vérifie une fois et quitte
# Usage: ajouter à crontab
#
# Exemple crontab:
# */5 9-12 * * 1-5 /home/USERNAME/cesar_ping/check_now.sh
# */5 13-17 * * 1-5 /home/USERNAME/cesar_ping/check_now.sh

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the bot once
python3 bot.py --webhook "$DISCORD_WEBHOOK_URL"
