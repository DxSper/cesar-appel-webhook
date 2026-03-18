import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Handles parsing data into Discord embeds and sending webhooks."""
    
    def __init__(self, webhook_url, role_id):
        self.webhook_url = webhook_url
        self.role_id = role_id
        self.base_url = 'https://cesar.emineo-informatique.fr'

    def send_attendance_alert(self, call_info):
        """Sends a notification that an attendance call has started or is active."""
        try:
            start_ts = call_info.get('start_date', 0) / 1000
            start_time = datetime.fromtimestamp(start_ts) if start_ts > 0 else datetime.now()
            
            teachers = call_info.get('teachers', [])
            teacher_names = ', '.join([f"{t.get('firstName', '')} {t.get('lastName', '')}" for t in teachers])
            
            embed = {
                "title": "🔔 Appel détecté sur César!",
                "url": self.base_url,
                "description": f"Une feuille d'émargement est disponible pour:\n**{call_info.get('description', 'Événement')}**",
                "color": 15158332,  # Red
                "fields": [
                    {
                        "name": "Lien",
                        "value": f"[Ouvrir César]({self.base_url})",
                        "inline": False
                    },
                    {
                        "name": "Heure",
                        "value": start_time.strftime('%H:%M'),
                        "inline": True
                    },
                    {
                        "name": "Signatures",
                        "value": f"{call_info.get('signed_count', 0)}/{call_info.get('total_students', 0)} étudiants",
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "Bot César"}
            }
            
            if teacher_names:
                embed["fields"].append({
                    "name": "Enseignant(s)",
                    "value": teacher_names,
                    "inline": False
                })
                
            payload = {
                "content": f"<@&{self.role_id}> 🎒 **Appel César disponible!**",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code in [200, 204]
            
        except Exception as e:
            logger.error(f"Error formatting/sending attendance alert: {e}")
            return False

    def send_schedule_notification(self, lessons):
        """Sends today's schedule at a specified hour."""
        try:
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
            
            if not lessons:
                embed = {
                    "title": f"📅 Emploi du temps — {today_str}",
                    "description": "🎉 **Pas de cours aujourd'hui !**",
                    "color": 5763719,  # Green
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {"text": "Bot César"}
                }
            else:
                description_lines = []
                for lesson in lessons:
                    start = lesson['start_time'].strftime('%H:%M')
                    end = lesson['end_time'].strftime('%H:%M')
                    subject = lesson['subject']
                    teachers = ', '.join(lesson['teachers']) if lesson['teachers'] else 'N/A'
                    rooms = ', '.join(lesson['rooms']) if lesson['rooms'] else 'N/A'
                    
                    remote_icon = '🏠' if lesson['remote'] else '🏫'
                    
                    line = f"{remote_icon} **{start} - {end}** │ {subject}\n"
                    line += f"   👤 {teachers} — 📍 {rooms}"
                    
                    if lesson.get('description'):
                        line += f"\n   📝 *{lesson['description']}*"
                    
                    description_lines.append(line)
                
                description = '\n\n'.join(description_lines)
                
                embed = {
                    "title": f"📅 Emploi du temps — {today_str}",
                    "description": description,
                    "color": 3447003,  # Blue
                    "footer": {"text": f"{len(lessons)} cours aujourd'hui"},
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            payload = {
                "content": f"<@&{self.role_id}> 📚 **Emploi du temps du jour**",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code in [200, 204]
            
        except Exception as e:
            logger.error(f"Error sending schedule notification: {e}")
            return False
