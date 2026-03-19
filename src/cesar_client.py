import os
import json
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CesarClient:
    """Handles communication with the César portal."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://cesar.emineo-informatique.fr'
        self.session = requests.Session()
        self.student_uuid = None

    def login(self):
        """Authenticates with the César portal and retrieves the student UUID."""
        try:
            r = self.session.get(self.base_url)
            if r.status_code != 200:
                logger.error(f"Failed to load login page: {r.status_code}")
                return False

            soup = BeautifulSoup(r.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf_token'})
            if not csrf_input:
                logger.error("Could not find CSRF token on login page")
                return False
            
            login_data = {
                '_username': self.username,
                '_password': self.password,
                '_csrf_token': csrf_input['value'],
                '_referer': '/'
            }
            
            r = self.session.post(f"{self.base_url}/connexion", data=login_data, allow_redirects=True)
            
            if 'déconnexion' in r.text.lower() or 'Se déconnecter' in r.text or 'studentRegistration' in r.text:
                logger.info("Login successful")
                
                # Extract student UUID
                soup = BeautifulSoup(r.text, 'html.parser')
                for el in soup.find_all(['div']):
                    attr = el.get('data-tui-calendar-student-registration-value')
                    if attr and isinstance(attr, str):
                        try:
                            reg_data = json.loads(attr)
                            self.student_uuid = reg_data.get('uuid')
                            logger.info(f"Student UUID loaded: {self.student_uuid}")
                            break
                        except json.JSONDecodeError:
                            continue
                return True
            else:
                logger.error("Login failed - invalid credentials or missing indicator")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def get_raw_events(self):
        """Fetches the raw events JSON array from the calendar."""
        try:
            r = self.session.get(f"{self.base_url}/emploi-du-temps")
            if r.status_code != 200:
                logger.error(f"Failed to fetch schedule page: {r.status_code}")
                return []
            
            events = []
            soup = BeautifulSoup(r.text, 'html.parser')
            for el in soup.find_all(['div']):
                attr = el.get('data-tui-calendar-event-lesson-schedules-value')
                if attr and isinstance(attr, str):
                    try:
                        events.extend(json.loads(attr))
                    except json.JSONDecodeError:
                        continue
            
            return events
        except Exception as e:
            logger.error(f"Error fetching raw events: {e}")
            return []

    def get_today_schedule(self):
        """
        Parses raw events to return today's lessons.
        Returns a list of dicts with subject, start_time, end_time, teachers, rooms, remote, description.
        """
        events = self.get_raw_events()
        today = datetime.now().date()
        today_lessons = []
        
        for evt in events:
            start_ts = evt.get('startDate', 0) / 1000
            end_ts = evt.get('endDate', 0) / 1000
            
            if start_ts <= 0:
                continue
            
            if datetime.fromtimestamp(start_ts).date() != today:
                continue
                
            if evt.get('lessonStatus') == 'Annulé':
                continue
                
            subject = evt.get('schoolSubject', {})
            teachers = evt.get('teachers', [])
            rooms = evt.get('rooms', [])
            
            lesson = {
                'subject': subject.get('name', 'Inconnu'),
                'start_time': datetime.fromtimestamp(start_ts),
                'end_time': datetime.fromtimestamp(end_ts),
                'teachers': [f"{t.get('firstName', '')} {t.get('lastName', '')}" for t in teachers],
                'rooms': [f"{rm.get('name', '')} ({rm.get('building', {}).get('name', '')})" for rm in rooms],
                'remote': evt.get('remote', False),
                'color': subject.get('colorPlanning', {}).get('hex', '#bfbfbf'),
                'description': evt.get('description', '').strip()
            }
            today_lessons.append(lesson)
            
        today_lessons.sort(key=lambda l: l['start_time'])
        return today_lessons

    def has_events_today(self):
        """Check if there are any classes scheduled for today."""
        today = datetime.now().date()
        events = self.get_raw_events()
        
        for evt in events:
            start_ts = evt.get('startDate', 0) / 1000
            if start_ts <= 0:
                continue
            if datetime.fromtimestamp(start_ts).date() == today:
                if evt.get('lessonStatus') != 'Annulé':
                    return True
        return False
    
    def get_next_event_end(self, events):
        """Get the end timestamp of the next upcoming event (or None if none)."""
        now = datetime.now()
        next_end = None
        
        for evt in events:
            end_ts = evt.get('endDate', 0) / 1000
            if end_ts <= 0:
                continue
            if datetime.fromtimestamp(end_ts) > now:
                if next_end is None or end_ts < next_end:
                    next_end = end_ts
                    
        return next_end
        
    def extract_active_calls(self, events):
        """
        Analyzes the list of events and returns those that have an active attendance 
        call requiring the student's signature.
        """
        active_calls = []
        now = datetime.now()
        
        for evt in events:
            end_ts = evt.get('endDate', 0) / 1000
            if end_ts < now.timestamp():
                continue  # Event ended
                
            att_sheet = evt.get('attendanceSheet')
            if not att_sheet:
                continue
                
            lines = att_sheet.get('attendanceSheetLines', [])
            
            # Find student's line and count signatures
            my_line = None
            signed_count = sum(1 for line in lines if line.get('signature') and line.get('signature', {}).get('signed') is True)
            
            for line in lines:
                reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                if reg.get('uuid') == self.student_uuid:
                    my_line = line
                    break
                    
            if my_line:
                sig = my_line.get('signature')
                att_without_sig = my_line.get('attendanceWithoutSignature', False)
                
                # Logic to detect if a call is active and needs our attention
                if sig is None and not att_without_sig:
                    # Attendance sheet exists → call is active, even with 0 signatures
                    active_calls.append(self._format_call_info(evt, lines, signed_count))
                elif sig is not None and sig.get('signed') is False:
                    # Signature block requested but not signed yet
                    active_calls.append(self._format_call_info(evt, lines, signed_count))
                    
        return active_calls
        
    def _format_call_info(self, evt, lines, signed_count):
        return {
            'uuid': evt.get('uuid'),
            'description': evt.get('description', 'Inconnu'),
            'lesson_type': evt.get('lessonType', ''),
            'start_date': evt.get('startDate', 0),
            'teachers': evt.get('teachers', []),
            'total_students': len(lines),
            'signed_count': signed_count
        }
