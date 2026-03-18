#!/bin/bash
# Script pour cron - lance une session du bot puis quitte
# Usage: ./check_now.sh [morning|afternoon]
#   morning  = 9:13 - 13:43
#   afternoon = 13:43 - 17:15

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

SESSION=${1:-morning}

case $SESSION in
    morning)
        echo "Starting morning session (9:13 - 13:43)"
        python3 main.py session \
            --start-hour 9 \
            --start-minute 13 \
            --end-hour 13 \
            --end-minute 43 \
            --check-interval 30
        ;;
    afternoon)
        echo "Starting afternoon session (13:43 - 17:15)"
        python3 main.py session \
            --start-hour 13 \
            --start-minute 43 \
            --end-hour 17 \
            --end-minute 15 \
            --check-interval 30
        ;;
    *)
        echo "Usage: $0 [morning|afternoon]"
        exit 1
        ;;
esac
