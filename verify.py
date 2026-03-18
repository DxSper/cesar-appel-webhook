#!/usr/bin/env python3
"""
Script de vérification rapide du bot César.
Teste la connexion et la détection d'appel sans envoyer de notification Discord.
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

def main():
    print("=" * 60)
    print("VÉRIFICATION DU BOT CÉSAR")
    print("=" * 60)
    print()

    # Session
    session = requests.Session()

    # 1. Login
    print("1. Connexion à César...")
    try:
        r = session.get(BASE_URL)
        soup = BeautifulSoup(r.text, 'html.parser')
        csrf = soup.find('input', {'name': '_csrf_token'})['value']

        login_data = {
            '_username': USERNAME,
            '_password': PASSWORD,
            '_csrf_token': csrf,
            '_referer': '/'
        }

        r = session.post(f'{BASE_URL}/connexion', data=login_data, allow_redirects=True)

        if 'déconnexion' in r.text.lower() or 'Se déconnecter' in r.text:
            print("   ✅ Connexion réussie")
        else:
            print("   ❌ Échec de connexion")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

    print()

    # 2. Récupérer l'UUID de l'étudiant
    print("2. Récupération de l'UUID étudiant...")
    soup = BeautifulSoup(r.text, 'html.parser')
    my_uuid = None
    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-student-registration-value')
        if attr and isinstance(attr, str):
            reg_data = json.loads(attr)
            my_uuid = reg_data.get('uuid')
            break

    if my_uuid:
        print(f"   ✅ UUID: {my_uuid}")
    else:
        print("   ❌ UUID non trouvé")
        return False

    print()

    # 3. Analyser les événements
    print("3. Analyse des événements du jour...")
    events_found = 0
    calls_detected = 0

    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-event-lesson-schedules-value')
        if attr and isinstance(attr, str):
            events = json.loads(attr)
            for evt in events:
                events_found += 1
                desc = evt.get('description', 'Inconnu')
                start_ts = evt.get('startDate', 0) / 1000
                end_ts = evt.get('endDate', 0) / 1000

                print(f"\n   Événement: {desc}")
                print(f"   Début: {datetime.fromtimestamp(start_ts) if start_ts else 'N/A'}")
                print(f"   Fin: {datetime.fromtimestamp(end_ts) if end_ts else 'N/A'}")

                # Check attendance sheet
                att_sheet = evt.get('attendanceSheet')
                if att_sheet:
                    lines = att_sheet.get('attendanceSheetLines', [])
                    print(f"   Attendance Sheet: ✅ Existe ({len(lines)} étudiants)")

                    # Find my line and count signed
                    my_line = None
                    signed_count = 0
                    for line in lines:
                        sig = line.get('signature')
                        if sig and sig.get('signed') is True:
                            signed_count += 1

                        student_reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                        if student_reg.get('uuid') == my_uuid:
                            my_line = line

                    print(f"   Étudiants signés: {signed_count}/{len(lines)}")

                    if my_line:
                        sig = my_line.get('signature')
                        sign_off = my_line.get('signingOff', False)
                        att_without_sig = my_line.get('attendanceWithoutSignature', False)

                        if sig is None:
                            if signed_count > 0:
                                print(f"   ⚠️  VOTRE ÉTAT: signature null, mais {signed_count} autres ont signé")
                                print(f"   ➡️  Le bot DEVRAIT vous notifier")
                                calls_detected += 1
                            else:
                                print(f"   ✅ VOTRE ÉTAT: signature null, aucun autre signé (appel pas lancé)")
                        elif sig.get('signed') is True:
                            print(f"   ✅ VOTRE ÉTAT: déjà signé")
                        else:
                            print(f"   ⚠️  VOTRE ÉTAT: signature existe mais signed=false")
                            calls_detected += 1
                else:
                    print(f"   Attendance Sheet: ❌ Aucune (pas encore lancée)")

    print()
    print(f"   → Total événements: {events_found}")
    print(f"   → Appels détectés: {calls_detected}")

    print()
    print("=" * 60)
    if calls_detected > 0:
        print("✅ RÉSULTAT: Des appels sont détectés, le bot fonctionnera !")
    else:
        print("ℹ️  RÉSULTAT: Aucun appel actif détecté (normal selon l'heure)")
    print("=" * 60)

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
        sys.exit(1)
