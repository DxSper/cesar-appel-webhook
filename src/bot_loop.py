import time
import logging
from datetime import datetime

from .cesar_client import CesarClient
from .discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)

class CesarAppelBot:
    """Manages the session-based application logic."""
    
    def __init__(self, username, password, webhook_url, role_id):
        self.client = CesarClient(username, password)
        self.notifier = DiscordNotifier(webhook_url, role_id)
        self.notified_events = set()

    def _check_and_notify_attendance(self):
        """Checks for active calls and notifies if not already done."""
        events = self.client.get_raw_events()
        active_calls = self.client.extract_active_calls(events)
        
        for call in active_calls:
            call_id = call['uuid']
            if call_id not in self.notified_events:
                logger.info(f"New attendance call detected: {call['description']}")
                if self.notifier.send_attendance_alert(call):
                    self.notified_events.add(call_id)
                    return True  # Signal que l'appel a été détecté et notifié
        return False  # Pas de nouvel appel

    def run_session(self, start_hour, start_minute, end_hour, end_minute, check_interval=30, send_schedule=False):
        """
        Run for one session (morning or afternoon), then exit.
        For use with cron: cron launches this, it runs and exits.
        
        Args:
            start_hour: Hour to start checking
            start_minute: Minute to start checking
            end_hour: Hour to stop checking
            end_minute: Minute to stop checking
            check_interval: Seconds between checks (default: 30)
            send_schedule: If True, send schedule notification first
        """
        logger.info(f"Session starting: {start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}")
        
        if not self.client.login():
            logger.error("Failed to login. Exiting.")
            return
        
        # Send schedule notification if requested (for 8h cron)
        if send_schedule:
            logger.info("Sending daily schedule notification...")
            lessons = self.client.get_today_schedule()
            self.notifier.send_schedule_notification(lessons)
            logger.info("Schedule sent. Exiting.")
            return  # Exit after sending schedule
        
        # Check if there are classes today
        if not self.client.has_events_today():
            logger.info("No classes scheduled for today. Exiting.")
            return
        
        end_time = datetime.now().replace(
            hour=end_hour, minute=end_minute, second=0, microsecond=0
        )
        
        # Main loop - run until end time or call detected
        while datetime.now() < end_time:
            # Check for attendance call
            call_detected = self._check_and_notify_attendance()
            
            # If a new call was detected and notified, exit immediately
            if call_detected:
                logger.info("Attendance call detected and notified. Exiting session.")
                return
            
            logger.debug(f"Sleeping {check_interval}s until next check")
            time.sleep(check_interval)
        
        logger.info(f"Session ended at {end_hour:02d}:{end_minute:02d}. Bot exiting.")

    def run_listener(self, check_interval=30):
        """
        Fast listener mode for continuous aggressive polling.
        """
        logger.info(f"Listener starting. Checking every {check_interval}s indefinitely.")
        
        if not self.client.login():
            logger.error("Failed to login. Exiting.")
            return
            
        try:
            while True:
                now = datetime.now()
                print(f"[{now.strftime('%H:%M:%S')}] Vérification...", end=" ", flush=True)
                
                events = self.client.get_raw_events()
                active_calls = self.client.extract_active_calls(events)
                
                if not active_calls:
                    print("Aucun appel actif")
                else:
                    for call in active_calls:
                        call_id = call['uuid']
                        if call_id not in self.notified_events:
                            print(f"\n🚀 APPEL DÉTECTÉ: {call['description']} ({datetime.fromtimestamp(call.get('start_date',0)/1000).strftime('%H:%M')})")
                            print(f"   Signatures: {call['signed_count']}/{call['total_students']}")
                            print("   Envoi notification Discord...", end=" ", flush=True)
                            
                            if self.notifier.send_attendance_alert(call):
                                print("✅ Envoyée!")
                                self.notified_events.add(call_id)
                            else:
                                print("❌ Erreur d'envoi")
                        else:
                            print("appel déjà notifié")
                            
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Surveillance arrêtée")
