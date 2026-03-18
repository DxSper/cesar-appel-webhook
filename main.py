#!/usr/bin/env python3
import sys
import os
import argparse
import logging
from dotenv import load_dotenv

from src.bot_loop import CesarAppelBot
from src.diagnostics import run_verify, run_full_test

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Credentials from environment variables
USERNAME = os.getenv('CESAR_USERNAME', '')
PASSWORD = os.getenv('CESAR_PASSWORD', '')
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
ROLE_ID = os.getenv('DISCORD_ROLE_ID', '1324662356868337775')

def main():
    parser = argparse.ArgumentParser(description='César Attendance Bot CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # 'run' command
    run_parser = subparsers.add_parser('run', help='Run the long-term daemon (morning/afternoon loops, daily schedule)')
    run_parser.add_argument('--start-hour', type=int, default=9, help='Morning start hour')
    run_parser.add_argument('--start-minute', type=int, default=13, help='Morning start minute')
    run_parser.add_argument('--afternoon-hour', type=int, default=13, help='Afternoon resume hour')
    run_parser.add_argument('--afternoon-minute', type=int, default=43, help='Afternoon resume minute')
    run_parser.add_argument('--schedule-hour', type=int, default=8, help='Hour to send daily schedule')
    run_parser.add_argument('--schedule-minute', type=int, default=0, help='Minute to send daily schedule')
    run_parser.add_argument('--check-interval', type=int, default=60, help='Seconds between checks')
    
    # 'listen' command
    listen_parser = subparsers.add_parser('listen', help='Aggressive 30s polling indefinitely')
    listen_parser.add_argument('--interval', type=int, default=30, help='Polling interval in seconds')

    # 'verify' command
    subparsers.add_parser('verify', help='Check status and active calls without sending to Discord')

    # 'test' command
    subparsers.add_parser('test', help='Do a full check and send a Discord test if call active')

    args = parser.parse_args()

    if not USERNAME or not PASSWORD:
        logger.error("Missing CESAR_USERNAME or CESAR_PASSWORD in .env")
        sys.exit(1)

    if args.command in ['run', 'listen', 'test'] and not WEBHOOK_URL:
        logger.error("Missing DISCORD_WEBHOOK_URL in .env")
        sys.exit(1)

    if args.command == 'run':
        bot = CesarAppelBot(USERNAME, PASSWORD, WEBHOOK_URL, ROLE_ID)
        bot.run_daemon(
            start_hour=args.start_hour,
            start_minute=args.start_minute,
            afternoon_hour=args.afternoon_hour,
            afternoon_minute=args.afternoon_minute,
            schedule_hour=args.schedule_hour,
            schedule_minute=args.schedule_minute,
            check_interval=args.check_interval
        )
    elif args.command == 'listen':
        bot = CesarAppelBot(USERNAME, PASSWORD, WEBHOOK_URL, ROLE_ID)
        bot.run_listener(check_interval=args.interval)
    elif args.command == 'verify':
        success = run_verify(USERNAME, PASSWORD)
        sys.exit(0 if success else 1)
    elif args.command == 'test':
        success = run_full_test(USERNAME, PASSWORD, WEBHOOK_URL, ROLE_ID)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
