#!/usr/bin/env python3
"""
César Attendance Call Bot
Monitors César school platform for attendance calls and sends Discord notifications.

Usage:
    python bot.py --webhook <discord_webhook_url>

Scheduling is handled by cron:
    # Morning session (9h13 - 13h43)
    13 9 * * 1-5 /path/to/check_now.sh
    
    # Afternoon session (13h43 - 18h)
    43 13 * * 1-5 /path/to/check_now.sh

The bot:
1. Runs continuously during its session (morning or afternoon)
2. Checks every 30 seconds for attendance calls
3. Sends Discord notification when call is detected
4. Exits at the end of the session
"""

import requests
import json
import sys
import time
import argparse
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging

# Load environment variables
from dotenv import load_dotenv
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

# Constants
BASE_URL = 'https://cesar.emineo-informatique.fr'
LOGIN_URL = f'{BASE_URL}/connexion'

# Credentials from environment variables
USERNAME = os.getenv('CESAR_USERNAME', '')
PASSWORD = os.getenv('CESAR_PASSWORD', '')
DISCORD_ROLE_ID = os.getenv('DISCORD_ROLE_ID', '1324662356868337775')


class CesarBot:
    def __init__(self, webhook_url, check_interval=30):
        """
        Initialize the bot.
        
        Args:
            webhook_url: Discord webhook URL for notifications
            check_interval: Seconds between checks (default: 30)
        """
        self.webhook_url = webhook_url
        self.check_interval = check_interval
        self.session = requests.Session()
        self.my_student_uuid = None
        self.notified_events = set()

    def login(self):
        """Login to César and save session cookies."""
        try:
            r = self.session.get(BASE_URL)
            soup = BeautifulSoup(r.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf_token'})
            
            if not csrf_input:
                logger.error("Could not find CSRF token on login page")
                return False
            
            csrf_token = csrf_input['value']
            
            login_data = {
                '_username': USERNAME,
                '_password': PASSWORD,
                '_csrf_token': csrf_token,
                '_referer': '/'
            }
            
            r = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
            
            if r.status_code != 200:
                logger.error(f"Login failed with status {r.status_code}")
                return False
            
            if 'déconnexion' in r.text.lower() or 'Se déconnecter' in r.text:
                logger.info("Login successful")
                
                soup = BeautifulSoup(r.text, 'html.parser')
                for el in soup.find_all(['div']):
                    attr = el.get('data-tui-calendar-student-registration-value')
                    if attr and isinstance(attr, str):
                        reg_data = json.loads(attr)
                        self.my_student_uuid = reg_data.get('uuid')
                        logger.info(f"My student UUID: {self.my_student_uuid}")
                        break
                
                return True
            else:
                logger.error("Login appears to have failed - no logout button found")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def check_attendance_calls(self):
        """Check for attendance calls on César homepage."""
        try:
            r = self.session.get(BASE_URL)
            if r.status_code != 200:
                logger.error(f"Failed to fetch homepage: {r.status_code}")
                return []
            
            soup = BeautifulSoup(r.text, 'html.parser')
            events_to_notify = []
            
            for el in soup.find_all(['div']):
                attr = el.get('data-tui-calendar-event-lesson-schedules-value')
                if attr and isinstance(attr, str):
                    try:
                        events = json.loads(attr)
                        for evt in events:
                            evt_uuid = evt.get('uuid')
                            if evt_uuid in self.notified_events:
                                continue
                            
                            end_ts = evt.get('endDate', 0) / 1000
                            if end_ts < datetime.now().timestamp():
                                continue
                            
                            att_sheet = evt.get('attendanceSheet')
                            if not att_sheet:
                                continue
                            
                            lines = att_sheet.get('attendanceSheetLines', [])
                            
                            my_line = None
                            for line in lines:
                                student_reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                                if student_reg.get('uuid') == self.my_student_uuid:
                                    my_line = line
                                    break
                            
                            if my_line:
                                signature = my_line.get('signature')
                                total_students = len(lines)
                                signed_students = sum(
                                    1 for line in lines 
                                    if line.get('signature') and line.get('signature', {}).get('signed') is True
                                )
                                
                                if signature is None:
                                    att_without_sig = my_line.get('attendanceWithoutSignature', False)
                                    if att_without_sig:
                                        logger.debug(f"Event {evt.get('description')}: Attendance without signature - skip")
                                    else:
                                        logger.info(f"Event {evt.get('description')}: Call active ({signed_students}/{total_students} signed)")
                                        event_info = {
                                            'uuid': evt_uuid,
                                            'description': evt.get('description', 'Unknown'),
                                            'lesson_type': evt.get('lessonType', ''),
                                            'start_date': evt.get('startDate', 0),
                                            'teachers': evt.get('teachers', [])
                                        }
                                        events_to_notify.append(event_info)
                                elif signature.get('signed') is False:
                                    event_info = {
                                        'uuid': evt_uuid,
                                        'description': evt.get('description', 'Unknown'),
                                        'lesson_type': evt.get('lessonType', ''),
                                        'start_date': evt.get('startDate', 0),
                                        'teachers': evt.get('teachers', [])
                                    }
                                    events_to_notify.append(event_info)
                                elif signature.get('signed') is True:
                                    logger.debug(f"Event {evt.get('description')}: Already signed - skipping")
                    except json.JSONDecodeError:
                        continue
            
            return events_to_notify
            
        except Exception as e:
            logger.error(f"Error checking attendance calls: {e}")
            return []

    def send_discord_notification(self, event_info):
        """Send Discord webhook notification for attendance call."""
        try:
            start_ts = event_info.get('start_date', 0) / 1000
            start_time = datetime.fromtimestamp(start_ts) if start_ts > 0 else datetime.now()
            
            teachers = event_info.get('teachers', [])
            teacher_names = ', '.join([f"{t.get('firstName', '')} {t.get('lastName', '')}" for t in teachers])
            
            embed = {
                "title": "🔔 Appel détecté sur César!",
                "url": BASE_URL,
                "description": f"Une feuille d'émargement est disponible pour:\n**{event_info.get('description', 'Événement')}**",
                "color": 15158332,
                "fields": [
                    {
                        "name": "Lien",
                        "value": f"[Ouvrir César]({BASE_URL})",
                        "inline": False
                    },
                    {
                        "name": "Type",
                        "value": event_info.get('lesson_type', 'Inconnu'),
                        "inline": True
                    },
                    {
                        "name": "Heure",
                        "value": start_time.strftime('%H:%M'),
                        "inline": True
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            if teacher_names:
                embed["fields"].append({
                    "name": "Enseignant(s)",
                    "value": teacher_names,
                    "inline": False
                })
            
            payload = {
                "content": f"<@&{DISCORD_ROLE_ID}> 🎒 **Appel César disponible**",
                "embeds": [embed]
            }
            
            response = self.session.post(self.webhook_url, json=payload)
            
            if response.status_code in [200, 204]:
                logger.info("Discord notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False

    def run(self, start_hour, start_minute, end_hour, end_minute):
        """
        Run the bot for one session.
        
        Args:
            start_hour: Hour to start checking
            start_minute: Minute to start checking
            end_hour: Hour to stop checking
            end_minute: Minute to stop checking
        """
        logger.info(f"Bot starting session: {start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}")
        
        if not self.login():
            logger.error("Failed to login. Exiting.")
            return
        
        end_time = datetime.now().replace(
            hour=end_hour, minute=end_minute, second=0, microsecond=0
        )
        
        # Wait until start time if not yet reached
        now = datetime.now()
        start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        if start_time < now:
            start_time += timedelta(days=1)
        
        if now < start_time:
            wait_seconds = (start_time - now).total_seconds()
            logger.info(f"Waiting {wait_seconds:.0f}s until {start_hour:02d}:{start_minute:02d}")
            time.sleep(min(wait_seconds, 300))
        
        # Main loop
        while datetime.now() < end_time:
            events = self.check_attendance_calls()
            
            for event in events:
                if event['uuid'] not in self.notified_events:
                    if self.send_discord_notification(event):
                        self.notified_events.add(event['uuid'])
            
            logger.debug(f"Sleeping {self.check_interval}s until next check")
            time.sleep(self.check_interval)
        
        logger.info(f"Session ended. Bot exiting.")


def main():
    parser = argparse.ArgumentParser(description='César attendance call bot')
    parser.add_argument('--webhook', required=True, help='Discord webhook URL')
    parser.add_argument('--start-hour', type=int, default=9, help='Start hour (default: 9)')
    parser.add_argument('--start-minute', type=int, default=13, help='Start minute (default: 13)')
    parser.add_argument('--end-hour', type=int, default=13, help='End hour (default: 13)')
    parser.add_argument('--end-minute', type=int, default=43, help='End minute (default: 43)')
    parser.add_argument('--check-interval', type=int, default=30, help='Check interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    bot = CesarBot(
        webhook_url=args.webhook,
        check_interval=args.check_interval
    )
    
    bot.run(
        start_hour=args.start_hour,
        start_minute=args.start_minute,
        end_hour=args.end_hour,
        end_minute=args.end_minute
    )


if __name__ == '__main__':
    main()
