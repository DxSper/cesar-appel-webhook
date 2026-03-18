#!/usr/bin/env python3
"""
Script de surveillance continue pour l'appel de l'après-midi.
Vérifie toutes les 30 secondes si l'appel est lancé.
"""

import sys
import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration from environment variables
USERNAME = os.getenv('CESAR_USERNAME', '')
PASSWORD = os.getenv('CESAR_PASSWORD', '')
BASE_URL = 'https://cesar.emineo-informatique.fr'
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
ROLE_ID = os.getenv('DISCORD_ROLE_ID', '1424662356868337775')

def login(session):
    """Connexion à César."""
    r = session.get(BASE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf_input = soup.find('input', {'name': '_csrf_token'})
    if not csrf_input:
        return None, None
    
    csrf = csrf_input['value']
    
    login_data = {
        '_username': USERNAME,
        '_password': PASSWORD,
        '_csrf_token': csrf,
        '_referer': '/'
    }
    
    r = session.post(f'{BASE_URL}/connexion', data=login_data, allow_redirects=True)
    
    # Récupérer UUID étudiant
    soup = BeautifulSoup(r.text, 'html.parser')
    my_uuid = None
    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-student-registration-value')
        if attr and isinstance(attr, str):
            reg_data = json.loads(attr)
            my_uuid = reg_data.get('uuid')
            break
    
    return r, my_uuid

def check_calls(session, my_uuid):
    """Vérifie les appels actifs."""
    r = session.get(BASE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    calls = []
    
    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-event-lesson-schedules-value')
        if attr and isinstance(attr, str):
            events = json.loads(attr)
            for evt in events:
                desc = evt.get('description', '')
                start_ts = evt.get('startDate', 0) / 1000
                teachers = evt.get('teachers', [])
                
                att_sheet = evt.get('attendanceSheet')
                if att_sheet:
                    lines = att_sheet.get('attendanceSheetLines', [])
                    
                    # Chercher ma ligne
                    for line in lines:
                        student_reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                        if student_reg.get('uuid') == my_uuid:
                            sig = line.get('signature')
                            
                            # Compter les signatures
                            signed_count = sum(1 for l in lines if l.get('signature') and l.get('signature', {}).get('signed'))
                            
                            # Si au moins un a signé et moi non = appel actif
                            if sig is None and signed_count > 0:
                                calls.append({
                                    'description': desc,
                                    'start_time': datetime.fromtimestamp(start_ts).strftime('%H:%M'),
                                    'teachers': teachers,
                                    'signed': f"{signed_count}/{len(lines)}"
                                })
                            break
    
    return calls

def send_discord(call):
    """Envoie la notification Discord."""
    teacher_names = ', '.join([f"{t.get('firstName')} {t.get('lastName')}" for t in call['teachers']])
    
    payload = {
        "content": f"<@&{ROLE_ID}> 🎒 **Appel César disponible!**",
        "embeds": [{
            "title": "🔔 Appel détecté sur César!",
            "description": f"Une feuille d'émargement est disponible pour:\n**{call['description']}**",
            "color": 15158332,
            "fields": [
                {
                    "name": "Heure",
                    "value": call['start_time'],
                    "inline": True
                },
                {
                    "name": "Signatures",
                    "value": f"{call['signed']} étudiants",
                    "inline": True
                }
            ],
            "footer": {"text": "Bot César - Surveillance active"}
        }]
    }
    
    if teacher_names:
        payload["embeds"][0]["fields"].append({
            "name": "Enseignant(s)",
            "value": teacher_names,
            "inline": False
        })
    
    return requests.post(WEBHOOK_URL, json=payload)

def main():
    print("=" * 60)
    print("SURVEILLANCE APPEL CÉSAR - APRÈS-MIDI")
    print("=" * 60)
    print()
    
    # Connexion
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connexion à César...")
    session = requests.Session()
    r, my_uuid = login(session)
    
    if not my_uuid:
        print("❌ Échec connexion")
        return
    
    print(f"✅ Connecté! UUID: {my_uuid}")
    print()
    print("📡 Surveillance active...")
    print("   Vérification toutes les 30 secondes")
    print("   Appuie sur Ctrl+C pour arrêter")
    print()
    
    notified = set()
    
    try:
        while True:
            now = datetime.now()
            print(f"[{now.strftime('%H:%M:%S')}] Vérification...", end=" ")
            
            calls = check_calls(session, my_uuid)
            
            if calls:
                for call in calls:
                    call_id = f"{call['description']}_{call['start_time']}"
                    
                    if call_id not in notified:
                        print(f"\n🚀 APPEL DÉTECTÉ: {call['description']} ({call['start_time']})")
                        print(f"   Signatures: {call['signed']}")
                        print(f"   Envoi notification Discord...", end=" ")
                        
                        resp = send_discord(call)
                        
                        if resp.status_code in [200, 204]:
                            print("✅ Envoyée!")
                            notified.add(call_id)
                        else:
                            print(f"❌ Erreur: {resp.status_code}")
                    else:
                        print("appel déjà notifié")
            
            if not calls:
                print("Aucun appel actif")
            
            import time
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Surveillance arrêtée")

if __name__ == '__main__':
    main()
