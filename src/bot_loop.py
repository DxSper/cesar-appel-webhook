import time
import logging
from datetime import datetime, timedelta

from .cesar_client import CesarClient
from .discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)

class CesarAppelBot:
    """Manages the long-running application logic loops."""
    
    def __init__(self, username, password, webhook_url, role_id):
        self.client = CesarClient(username, password)
        self.notifier = DiscordNotifier(webhook_url, role_id)
        self.notified_events = set()
        self.schedule_sent_date = None

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

    def run_daemon(self, start_hour=9, start_minute=13, afternoon_hour=13, afternoon_minute=43, schedule_hour=8, schedule_minute=0, check_interval=60):
        """
        Main daemon loop that respects class hours to save resources.
        Sleeps until start_time, checks during morning, sleeps until afternoon_time, checks during afternoon.
        """
        logger.info(f"Daemon starting. Check interval: {check_interval}s")
        logger.info(f"Daily schedule will be sent at {schedule_hour:02d}:{schedule_minute:02d}")
        
        if not self.client.login():
            logger.error("Failed to login. Exiting.")
            return

        while True:
            now = datetime.now()
            
            # --- Daily schedule notification ---
            today = now.date()
            if (self.schedule_sent_date != today 
                and now.hour >= schedule_hour 
                and (now.hour > schedule_hour or now.minute >= schedule_minute)):
                
                logger.info("Sending daily schedule notification...")
                lessons = self.client.get_today_schedule()
                if self.notifier.send_schedule_notification(lessons):
                    self.schedule_sent_date = today
                    logger.info(f"Schedule sent for {today}")
                else:
                    logger.warning("Failed to send schedule, will retry next loop")
            
            # --- Attendance Monitoring Logic ---
            if now.hour < start_hour or (now.hour == start_hour and now.minute < start_minute):
                # Before start time - wait until morning start
                target_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                if target_time < now:
                    target_time += timedelta(days=1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"Waiting {wait_seconds:.0f}s until {start_hour:02d}:{start_minute:02d}")
                time.sleep(min(wait_seconds, 300))  # Sleep in chunks
                
            elif now.hour >= start_hour and now.hour < afternoon_hour:
                # Morning checking phase
                logger.debug("Morning checking phase")
                self._check_and_notify_attendance()
                time.sleep(check_interval)
                
            elif now.hour == afternoon_hour and now.minute < afternoon_minute:
                # Afternoon pre-sleep phase
                logger.debug("Preparing for afternoon sleep...")
                self._check_and_notify_attendance()
                time.sleep(check_interval)
                
            else:
                # Afternoon sleep phase (classes over or afternoon gap)
                wake_hour = start_hour
                wake_minute = start_minute
                
                if now.hour > afternoon_hour or (now.hour == afternoon_hour and now.minute >= afternoon_minute):
                    # Sleep until next day
                    wake_time = now.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
                    wake_time += timedelta(days=1)
                else:
                    wake_time = now.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
                    if wake_time < now:
                        wake_time += timedelta(days=1)
                
                wait_seconds = (wake_time - now).total_seconds()
                logger.info(f"Sleeping for {wait_seconds:.0f}s until next morning")
                
                sleep_start = datetime.now()
                while (datetime.now() - sleep_start).total_seconds() < wait_seconds:
                    time.sleep(300)

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
