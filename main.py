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

# === Credentials (required) ===
USERNAME = os.getenv('CESAR_USERNAME', '')
PASSWORD = os.getenv('CESAR_PASSWORD', '')
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
ROLE_ID = os.getenv('DISCORD_ROLE_ID', '1324662356868337775')

# === Scheduling (from .env with defaults) ===
BOT_START_HOUR = int(os.getenv('BOT_START_HOUR', '9'))
BOT_START_MINUTE = int(os.getenv('BOT_START_MINUTE', '13'))
BOT_END_HOUR = int(os.getenv('BOT_END_HOUR', '13'))
BOT_END_MINUTE = int(os.getenv('BOT_END_MINUTE', '43'))
BOT_AFTERNOON_START_HOUR = int(os.getenv('BOT_AFTERNOON_START_HOUR', '13'))
BOT_AFTERNOON_START_MINUTE = int(os.getenv('BOT_AFTERNOON_START_MINUTE', '43'))
BOT_AFTERNOON_END_HOUR = int(os.getenv('BOT_AFTERNOON_END_HOUR', '17'))
BOT_AFTERNOON_END_MINUTE = int(os.getenv('BOT_AFTERNOON_END_MINUTE', '15'))
BOT_CHECK_INTERVAL = int(os.getenv('BOT_CHECK_INTERVAL', '30'))
SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR', '8'))
SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', '0'))


def main():
    parser = argparse.ArgumentParser(description='César Attendance Bot CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # 'run' command (daemon)
    subparsers.add_parser('run', help='Run the long-term daemon')
    
    # 'session' command (for cron)
    session_parser = subparsers.add_parser('session', help='Run for one session then exit (for cron)')
    session_parser.add_argument('type', nargs='?', choices=['morning', 'afternoon'], default='morning',
                               help='Session type: morning or afternoon (default: morning)')

    # 'listen' command
    subparsers.add_parser('listen', help='Aggressive continuous polling')

    # 'verify' command
    subparsers.add_parser('verify', help='Check status without sending notification')

    # 'test' command
    subparsers.add_parser('test', help='Full check with Discord notification if call active')

    args = parser.parse_args()

    # Validate required credentials
    if not USERNAME or not PASSWORD:
        logger.error("Missing CESAR_USERNAME or CESAR_PASSWORD in .env")
        sys.exit(1)

    if args.command in ['run', 'listen', 'test', 'session'] and not WEBHOOK_URL:
        logger.error("Missing DISCORD_WEBHOOK_URL in .env")
        sys.exit(1)

    bot = CesarAppelBot(USERNAME, PASSWORD, WEBHOOK_URL, ROLE_ID)

    if args.command == 'run':
        bot.run_daemon(
            start_hour=BOT_START_HOUR,
            start_minute=BOT_START_MINUTE,
            afternoon_hour=BOT_AFTERNOON_START_HOUR,
            afternoon_minute=BOT_AFTERNOON_START_MINUTE,
            schedule_hour=SCHEDULE_HOUR,
            schedule_minute=SCHEDULE_MINUTE,
            check_interval=BOT_CHECK_INTERVAL
        )
    elif args.command == 'session':
        if args.type == 'morning':
            bot.run_session(
                start_hour=BOT_START_HOUR,
                start_minute=BOT_START_MINUTE,
                end_hour=BOT_END_HOUR,
                end_minute=BOT_END_MINUTE,
                check_interval=BOT_CHECK_INTERVAL
            )
        else:  # afternoon
            bot.run_session(
                start_hour=BOT_AFTERNOON_START_HOUR,
                start_minute=BOT_AFTERNOON_START_MINUTE,
                end_hour=BOT_AFTERNOON_END_HOUR,
                end_minute=BOT_AFTERNOON_END_MINUTE,
                check_interval=BOT_CHECK_INTERVAL
            )
    elif args.command == 'listen':
        bot.run_listener(check_interval=BOT_CHECK_INTERVAL)
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
