import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from instagrapi import Client

try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, ChallengeRequired
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    Client = None  # type: ignore
    LoginRequired = Exception
    ChallengeRequired = Exception
    INSTAGRAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


class InstagramNotifier:
    """
    Handles sending notifications via Instagram DM using instagrapi.
    Manages session persistence to handle 2FA automatically.
    """
    
    SESSION_FILE = Path.home() / '.cesar-bot' / 'instagram_session.json'
    
    def __init__(self, username, password, target_thread_id=None):
        self.username = username
        self.password = password
        self.target_thread_id = target_thread_id
        self.client = None
        
        # Ensure session directory exists
        self.SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_client(self):
        """Get or create Instagram client with session management."""
        if not INSTAGRAPI_AVAILABLE:
            logger.error("instagrapi not installed. Run: pip install instagrapi")
            return None
        
        if self.client is not None:
            return self.client
        
        client = Client()
        
        # Try to load existing session
        if self.SESSION_FILE.exists():
            try:
                client.load_settings(self.SESSION_FILE)
                logger.info("Loaded existing Instagram session")
                
                # Verify session is still valid
                try:
                    client.user_info(client.user_id)
                    logger.info("Session is valid")
                    self.client = client
                    return self.client
                except LoginRequired:
                    logger.info("Session expired, logging in again...")
                    client = Client()
            except Exception as e:
                logger.warning(f"Could not load session: {e}")
                client = Client()
        
        # Login with password
        try:
            logger.info(f"Logging in to Instagram as {self.username}...")
            client.login(self.username, self.password)
            
            # Save session for next time
            client.dump_settings(self.SESSION_FILE)
            logger.info("Login successful, session saved")
            
            self.client = client
            return self.client
            
        except ChallengeRequired as e:
            logger.error(f"Challenge required (2FA or email verification): {e}")
            logger.info("Please complete verification and try again")
            return None
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return None
    
    def send_message(self, message, thread_id=None):
        """
        Send a DM message to the target thread.
        
        Args:
            message: Text message to send
            thread_id: Optional thread ID (overrides default)
        
        Returns:
            bool: True if sent successfully
        """
        target = thread_id or self.target_thread_id
        
        if not target:
            logger.error("No thread_id provided")
            return False
        
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.direct_send(message, thread_ids=[int(target)])
            logger.info(f"DM sent successfully to thread {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to send DM: {e}")
            return False
    
    def send_attendance_alert(self, call_info):
        """Send attendance call alert to Instagram."""
        start_ts = call_info.get('start_date', 0) / 1000
        start_time = datetime.fromtimestamp(start_ts) if start_ts > 0 else datetime.now()
        
        teachers = call_info.get('teachers', [])
        teacher_names = ', '.join([f"{t.get('firstName', '')} {t.get('lastName', '')}" for t in teachers])
        
        message = (
            f"🔔 APPEL DÉTECTÉ SUR CÉSAR!\n\n"
            f"📚 {call_info.get('description', 'Événement')}\n"
            f"🕐 {start_time.strftime('%H:%M')}\n"
            f"✍️ {call_info.get('signed_count', 0)}/{call_info.get('total_students', 0)} signatures\n"
        )
        
        if teacher_names:
            message += f"👤 {teacher_names}\n"
        
        message += f"\n👉 Signes vite! {call_info.get('signed_count', 0)} personnes ont déjà signé!"
        
        return self.send_message(message)
    
    def send_schedule_notification(self, lessons):
        """Send today's schedule to Instagram."""
        today_str = datetime.now().strftime('%A %d %B %Y')
        
        day_map = {
            'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
        }
        month_map = {
            'January': 'janvier', 'February': 'février', 'March': 'mars',
            'April': 'avril', 'May': 'mai', 'June': 'juin',
            'July': 'juillet', 'August': 'août', 'September': 'septembre',
            'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
        }
        for en, fr in day_map.items():
            today_str = today_str.replace(en, fr)
        for en, fr in month_map.items():
            today_str = today_str.replace(en, fr)
        
        message = f"📅 EMPLOI DU TEMPS - {today_str}\n\n"
        
        if not lessons:
            message += "🎉 Pas de cours aujourd'hui!"
        else:
            for lesson in lessons:
                start = lesson['start_time'].strftime('%H:%M')
                end = lesson['end_time'].strftime('%H:%M')
                subject = lesson['subject']
                remote_icon = '🏠' if lesson['remote'] else '🏫'
                
                message += f"{remote_icon} {start}-{end} │ {subject}\n"
        
        return self.send_message(message)
    
    def logout(self):
        """Logout and clear session."""
        if self.client:
            try:
                self.client.logout()
                if self.SESSION_FILE.exists():
                    self.SESSION_FILE.unlink()
                logger.info("Logged out from Instagram")
            except Exception as e:
                logger.warning(f"Logout warning: {e}")
            finally:
                self.client = None
