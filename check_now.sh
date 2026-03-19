#!/bin/bash
# Script pour cron - lance une session du bot puis quitte
# Les horaires sont définis dans .env (BOT_START_HOUR, BOT_START_MINUTE, etc.)
# Usage: ./check_now.sh [morning|afternoon|schedule]

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

SESSION=${1:-morning}

case $SESSION in
    schedule)
        echo "Sending daily schedule..."
        python3 main.py session schedule
        ;;
    morning)
        echo "Starting morning session (${BOT_START_HOUR:-9}:${BOT_START_MINUTE:-13} - ${BOT_END_HOUR:-13}:${BOT_END_MINUTE:-43})"
        python3 main.py session morning
        ;;
    afternoon)
        echo "Starting afternoon session (${BOT_AFTERNOON_START_HOUR:-13}:${BOT_AFTERNOON_START_MINUTE:-43} - ${BOT_AFTERNOON_END_HOUR:-17}:${BOT_AFTERNOON_END_MINUTE:-15})"
        python3 main.py session afternoon
        ;;
    *)
        echo "Usage: $0 [morning|afternoon|schedule]"
        exit 1
        ;;
esac
