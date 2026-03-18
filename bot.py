#!/usr/bin/env python3
"""
César Attendance Call Bot
Monitors César school platform for attendance calls and sends Discord notifications.

Usage (cron mode - run once):
    python bot.py --webhook <discord_webhook_url>

Usage (continuous mode - systemd):
    python bot.py --webhook <discord_webhook_url> --continuous

The bot checks for attendance calls and sends Discord notification when detected.
- Default (cron): Runs once and exits. Use cron to schedule periodic checks.
- --continuous: Runs continuously with internal scheduling (for systemd/service).
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
    def __init__(self, webhook_url, check_interval=60):
        """
        Initialize the bot.
        
        Args:
            webhook_url: Discord webhook URL for notifications
            check_interval: Seconds between checks (default: 60)
        """
        self.webhook_url = webhook_url
        self.check_interval = check_interval
        self.session = requests.Session()
        self.my_student_uuid = None
        self.last_checked = None
        self.notified_events = set()  # Track which events we've already notified about

    def login(self):
        """Login to César and save session cookies."""
        try:
            # Get CSRF token
            r = self.session.get(BASE_URL)
            soup = BeautifulSoup(r.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf_token'})
            
            if not csrf_input:
                logger.error("Could not find CSRF token on login page")
                return False
            
            csrf_token = csrf_input['value']
            
            # Perform login
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
            
            # Verify login success by checking for logout link or user name
            if 'déconnexion' in r.text.lower() or 'Se déconnecter' in r.text:
                logger.info("Login successful")
                
                # Get my student registration UUID
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
        """
        Check for attendance calls on César homepage.
        
        Returns:
            list: Events with attendance calls that need notification
        """
        try:
            r = self.session.get(BASE_URL)
            if r.status_code != 200:
                logger.error(f"Failed to fetch homepage: {r.status_code}")
                return []
            
            soup = BeautifulSoup(r.text, 'html.parser')
            events_to_notify = []
            
            # Parse event data from the calendar
            for el in soup.find_all(['div']):
                attr = el.get('data-tui-calendar-event-lesson-schedules-value')
                if attr and isinstance(attr, str):
                    try:
                        events = json.loads(attr)
                        for evt in events:
                            # Skip if we've already notified about this event
                            evt_uuid = evt.get('uuid')
                            if evt_uuid in self.notified_events:
                                continue
                            
                            # Skip if event has already ended
                            end_ts = evt.get('endDate', 0) / 1000
                            if end_ts < datetime.now().timestamp():
                                logger.debug(f"Event {evt.get('description')}: Event already ended - skipping")
                                continue
                            
                            # Check for attendance sheet
                            att_sheet = evt.get('attendanceSheet')
                            if not att_sheet:
                                continue
                            
                            # Check for attendance sheet lines (student signatures)
                            lines = att_sheet.get('attendanceSheetLines', [])
                            
                            # Find my signature line
                            my_line = None
                            for line in lines:
                                student_reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                                if student_reg.get('uuid') == self.my_student_uuid:
                                    my_line = line
                                    break
                            
                            if my_line:
                                signature = my_line.get('signature')
                                signing_off = my_line.get('signingOff', False)
                                
                                # Logic for detecting attendance call:
                                # 1. attendanceSheet exists but my signature is null = "call will be launched soon" or "call not yet active"
                                # 2. attendanceSheet exists + signature exists + signed=false + signingOff=true = "call is active, waiting for signature"
                                # 3. attendanceSheet exists + signature exists + signed=true = "I've already signed"
                                
                                if signature is None:
                                    # Ma signature est null - je n'ai pas encore signé
                                    # signingOff=true indique que l'appel est actif (feuille fermée pour signature)
                                    
                                    # Compter les signatures
                                    total_students = len(att_sheet.get('attendanceSheetLines', []))
                                    signed_students = sum(1 for line in att_sheet.get('attendanceSheetLines', []) 
                                                         if line.get('signature') and line.get('signature', {}).get('signed') is True)
                                    
                                    # Vérifier attendanceWithoutSignature
                                    att_without_sig = my_line.get('attendanceWithoutSignature', False)
                                    if att_without_sig:
                                        logger.debug(f"Event {evt.get('description')}: Attendance without signature - skip")
                                    else:
                                        # L'appel est actif (signingOff=true) et je dois signer
                                        # On notifie que l'appel soit lancé (0 ou plusieurs signatures)
                                        logger.info(f"Event {evt.get('description')}: Call active ({signed_students}/{total_students} signed)")
                                        
                                        event_info = {
                                            'uuid': evt_uuid,
                                            'description': evt.get('description', 'Unknown'),
                                            'lesson_type': evt.get('lessonType', ''),
                                            'start_date': evt.get('startDate', 0),
                                            'teachers': evt.get('teachers', [])
                                        }
                                        events_to_notify.append(event_info)
                                        logger.info(f"Attendance call detected: {event_info['description']}")
                                    continue
                                elif signature.get('signed') is False:
                                    # Signature exists but not signed yet - call is active!
                                    event_info = {
                                        'uuid': evt_uuid,
                                        'description': evt.get('description', 'Unknown'),
                                        'lesson_type': evt.get('lessonType', ''),
                                        'start_date': evt.get('startDate', 0),
                                        'teachers': evt.get('teachers', [])
                                    }
                                    events_to_notify.append(event_info)
                                    logger.info(f"Attendance call detected: {event_info['description']}")
                                elif signature.get('signed') is True:
                                    logger.debug(f"Event {evt.get('description')}: Already signed - skipping")
                    except json.JSONDecodeError as e:
                        logger.debug(f"Failed to parse event data: {e}")
                        continue
            
            return events_to_notify
            
        except Exception as e:
            logger.error(f"Error checking attendance calls: {e}")
            return []

    def send_discord_notification(self, event_info):
        """Send Discord webhook notification for attendance call."""
        try:
            # Format timestamp
            start_ts = event_info.get('start_date', 0) / 1000
            start_time = datetime.fromtimestamp(start_ts) if start_ts > 0 else datetime.now()
            
            # Format teachers
            teachers = event_info.get('teachers', [])
            teacher_names = ', '.join([f"{t.get('firstName', '')} {t.get('lastName', '')}" for t in teachers])
            
            embed = {
                "title": "🔔 Appel détecté sur César!",
                "url": BASE_URL,
                "description": f"Une feuille d'émargement est disponible pour:\n**{event_info.get('description', 'Événement')}**",
                "color": 15158332,  # Red color
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
            
            # Mention le rôle Discord
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

    def check_once(self):
        """Run a single check and exit. For cron jobs."""
        logger.info("Running single check...")
        
        if not self.login():
            logger.error("Failed to login. Exiting.")
            return False
        
        events = self.check_attendance_calls()
        
        for event in events:
            if event['uuid'] not in self.notified_events:
                if self.send_discord_notification(event):
                    self.notified_events.add(event['uuid'])
        
        logger.info("Check complete.")
        return True
    
    def run_continuous(self, start_hour=9, start_minute=13, afternoon_hour=13, afternoon_minute=43):
        """
        Continuous monitoring mode (for systemd/service).
        Keeps running and sleeping, checking periodically.
        
        Args:
            start_hour: Hour to start checking (default: 9)
            start_minute: Minute to start checking (default: 13)
            afternoon_hour: Hour to resume after sleep (default: 13)
            afternoon_minute: Minute to resume after sleep (default: 43)
        """
        logger.info(f"Bot starting in continuous mode.")
        
        if not self.login():
            logger.error("Failed to login. Exiting.")
            return
        
        while True:
            now = datetime.now()
            
            # Determine current phase
            if now.hour < start_hour or (now.hour == start_hour and now.minute < start_minute):
                # Before start time - wait until start time
                target_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                if target_time < now:
                    target_time += timedelta(days=1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"Waiting {wait_seconds:.0f}s until {start_hour:02d}:{start_minute:02d}")
                time.sleep(min(wait_seconds, 300))  # Sleep in chunks
                
            elif now.hour >= start_hour and now.hour < afternoon_hour:
                # Morning checking phase
                logger.debug("Morning checking phase")
                events = self.check_attendance_calls()
                
                for event in events:
                    if event['uuid'] not in self.notified_events:
                        if self.send_discord_notification(event):
                            self.notified_events.add(event['uuid'])
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            elif now.hour == afternoon_hour and now.minute < afternoon_minute:
                # Afternoon pre-sleep phase
                logger.info("Preparing for afternoon sleep...")
                # Continue checking until afternoon sleep time
                events = self.check_attendance_calls()
                
                for event in events:
                    if event['uuid'] not in self.notified_events:
                        if self.send_discord_notification(event):
                            self.notified_events.add(event['uuid'])
                
                time.sleep(self.check_interval)
                
            else:
                # Afternoon sleep phase - wait until next morning
                wake_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                wake_time += timedelta(days=1)
                
                wait_seconds = (wake_time - now).total_seconds()
                logger.info(f"Sleeping for {wait_seconds:.0f}s until next morning")
                
                # Sleep in chunks to allow for graceful shutdown
                sleep_start = datetime.now()
                while (datetime.now() - sleep_start).total_seconds() < wait_seconds:
                    time.sleep(300)  # Sleep 5 minutes at a time


def main():
    parser = argparse.ArgumentParser(description='César attendance call bot')
    parser.add_argument('--webhook', required=True, help='Discord webhook URL')
    parser.add_argument('--continuous', action='store_true', help='Run continuously (for systemd). Default: run once and exit (for cron)')
    parser.add_argument('--check-interval', type=int, default=60, help='Check interval in seconds (default: 60, only for continuous mode)')
    
    args = parser.parse_args()
    
    bot = CesarBot(
        webhook_url=args.webhook,
        check_interval=args.check_interval
    )
    
    if args.continuous:
        bot.run_continuous()
    else:
        bot.check_once()


if __name__ == '__main__':
    main()
