#!/usr/bin/env python3
"""
Test script for César attendance bot.
Tests the bot logic without sending actual Discord notifications.
"""

import sys
import json
import logging
from datetime import datetime
from bot import CesarBot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_bot():
    """Test the bot logic comprehensively."""
    print("=" * 60)
    print("TEST DU BOT CÉSAR - SURVEILLANCE DES APPELS")
    print("=" * 60)
    print()

    # Create bot with dummy webhook
    bot = CesarBot(webhook_url='dummy', check_interval=60)

    # Test 1: Login
    print("TEST 1: Connexion à César")
    print("-" * 40)
    if bot.login():
        print("✓ Login successful!")
        print(f"✓ Student UUID: {bot.my_student_uuid}")
    else:
        print("✗ Login failed")
        return False
    print()

    # Test 2: Check current events
    print("TEST 2: Analyse des événements actuels")
    print("-" * 40)
    import requests
    from bs4 import BeautifulSoup

    r = bot.session.get('https://cesar.emineo-informatique.fr')
    soup = BeautifulSoup(r.text, 'html.parser')

    events_found = 0
    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-event-lesson-schedules-value')
        if attr and isinstance(attr, str):
            events = json.loads(attr)
            for evt in events:
                events_found += 1
                desc = evt.get('description', 'Inconnu')
                start_ts = evt.get('startDate', 0) / 1000
                end_ts = evt.get('endDate', 0) / 1000

                print(f"Événement: {desc}")
                print(f"  Début: {datetime.fromtimestamp(start_ts) if start_ts else 'N/A'}")
                print(f"  Fin: {datetime.fromtimestamp(end_ts) if end_ts else 'N/A'}")

                # Check attendance sheet
                att_sheet = evt.get('attendanceSheet')
                if att_sheet:
                    lines = att_sheet.get('attendanceSheetLines', [])
                    print(f"  Attendance Sheet: {att_sheet.get('uuid')}")
                    print(f"  Étudiants dans la feuille: {len(lines)}")

                    # Find my line
                    for line in lines:
                        student_reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                        if student_reg.get('uuid') == bot.my_student_uuid:
                            sig = line.get('signature')
                            sign_off = line.get('signingOff', False)
                            att_without_sig = line.get('attendanceWithoutSignature', False)

                            print(f"  [MON ÉTAT]")
                            print(f"    signingOff: {sign_off}")
                            print(f"    attendanceWithoutSignature: {att_without_sig}")
                            if sig:
                                print(f"    signature.signed: {sig.get('signed', 'N/A')}")
                                print(f"    signature.uuid: {sig.get('uuid')}")
                            else:
                                print(f"    signature: null")
                            break
                else:
                    print(f"  Attendance Sheet: Aucune (pas encore lancée)")
                print()

    if events_found == 0:
        print("Aucun événement trouvé sur la page d'accueil")
    print()

    # Test 3: Check bot detection
    print("TEST 3: Détection des appels par le bot")
    print("-" * 40)
    events = bot.check_attendance_calls()
    print(f"Événements détectés: {len(events)}")
    for evt in events:
        print(f"  - {evt.get('description')} ({evt.get('lesson_type')})")
    print()

    # Test 4: Explain logic
    print("TEST 4: Explication de la logique de détection")
    print("-" * 40)
    print("Le bot détecte un appel lorsque:")
    print("  1. Une attendance sheet existe")
    print("  2. ET l'étudiant a une ligne dans cette feuille")
    print("  3. ET l'une des conditions suivantes est vraie:")
    print("     a) signature est null ET signingOff=true (appel vient d'être lancé)")
    print("     b) signature existe ET signed=false (appel en cours, pas signé)")
    print()

    # Test 5: State matrix
    print("TEST 5: Matrice des états possibles")
    print("-" * 40)
    print("""
État | Attendance Sheet | signingOff | signature.signed | Détection ?
-----|------------------|------------|------------------|-----------
  1  | Aucune           | -          | -                | NON (pas encore prêt)
  2  | Existe           | false      | null             | NON (appel pas lancé)
  3  | Existe           | true       | null             | OUI (appel vient d'être lancé)
  4  | Existe           | true       | false            | OUI (appel en cours, pas signé)
  5  | Existe           | true       | true             | NON (déjà signé)
    """)
    print()

    print("=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = test_bot()
    sys.exit(0 if success else 1)
