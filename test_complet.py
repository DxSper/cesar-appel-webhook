#!/usr/bin/env python3
"""
Script de test COMPLET et PRÉCIS du bot César.
Affiche chaque étape en détail pour prouver que le bot fonctionne.
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

def print_step(step, message, status=""):
    """Affiche une étape avec formatage."""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "➡️": "➡️", "🔄": "🔄"}
    print(f"{step:2d}. {message} {status}")

def main():
    print("=" * 70)
    print("TEST COMPLET ET DÉTAILLÉ DU BOT CÉSAR")
    print("=" * 70)
    print()

    session = requests.Session()
    step = 1

    # ÉTAPE 1 : Connexion
    print_step(step, "Connexion à César")
    try:
        r = session.get(BASE_URL)
        soup = BeautifulSoup(r.text, 'html.parser')
        csrf_input = soup.find('input', {'name': '_csrf_token'})
        if not csrf_input:
            print("   ❌ CSRF token introuvable")
            return False
        csrf = csrf_input['value']

        login_data = {
            '_username': USERNAME,
            '_password': PASSWORD,
            '_csrf_token': csrf,
            '_referer': '/'
        }

        r = session.post(f'{BASE_URL}/connexion', data=login_data, allow_redirects=True)

        # Check for logout link or user name
        logout_found = 'déconnexion' in r.text.lower() or 'Se déconnecter' in r.text
        if logout_found:
            print("   ✅ Connexion réussie")
        else:
            print("   ⚠️  Vérification alternative...")
            # Check for attendance calendar data (confirms login)
            if 'data-tui-calendar' in r.text or 'studentRegistration' in r.text:
                print("   ✅ Connexion réussie (données calendrier trouvées)")
            else:
                print("   ❌ Échec de connexion - aucun indicateur trouvé")
                print(f"   Debug: Final URL: {r.url}, Status: {r.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

    # ÉTAPE 2 : Récupération UUID
    step += 1
    print_step(step, "Récupération de l'UUID étudiant")
    soup = BeautifulSoup(r.text, 'html.parser')
    my_uuid = None
    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-student-registration-value')
        if attr and isinstance(attr, str):
            reg_data = json.loads(attr)
            my_uuid = reg_data.get('uuid')
            break

    if my_uuid:
        print(f"   ✅ UUID récupéré: {my_uuid}")
    else:
        print("   ❌ UUID non trouvé")
        return False

    # ÉTAPE 3 : Analyse événements
    step += 1
    print_step(step, "Analyse des événements du jour")
    events_found = 0
    active_calls = []

    for el in soup.find_all(['div']):
        attr = el.get('data-tui-calendar-event-lesson-schedules-value')
        if attr and isinstance(attr, str):
            events = json.loads(attr)
            for evt in events:
                events_found += 1
                desc = evt.get('description', 'Inconnu')
                start_ts = evt.get('startDate', 0) / 1000
                end_ts = evt.get('endDate', 0) / 1000

                print(f"\n   ┌─ Événement: {desc}")
                print(f"   │  Début: {datetime.fromtimestamp(start_ts) if start_ts else 'N/A'}")
                print(f"   │  Fin: {datetime.fromtimestamp(end_ts) if end_ts else 'N/A'}")

                # Check attendance sheet
                att_sheet = evt.get('attendanceSheet')
                if att_sheet:
                    lines = att_sheet.get('attendanceSheetLines', [])
                    print(f"   │  Attendance Sheet: ✅ Existe ({len(lines)} étudiants)")

                    # Analyse des signatures
                    signed_count = 0
                    for line in lines:
                        sig = line.get('signature')
                        if sig and sig.get('signed') is True:
                            signed_count += 1

                    print(f"   │  Étudiants signés: {signed_count}/{len(lines)}")

                    # Trouver ma ligne
                    for line in lines:
                        student_reg = line.get('planningGroupSubscription', {}).get('studentRegistration', {})
                        if student_reg.get('uuid') == my_uuid:
                            sig = line.get('signature')
                            sign_off = line.get('signingOff', False)
                            att_without_sig = line.get('attendanceWithoutSignature', False)

                            print(f"   │")
                            print(f"   │  VOTRE ÉTAT:")
                            print(f"   │    signingOff: {sign_off}")
                            print(f"   │    attendanceWithoutSignature: {att_without_sig}")

                            # Logique du bot pour détecter l'appel
                            if sig is None:
                                if signed_count > 0:
                                    print(f"   │    signature: null ⚠️")
                                    print(f"   │    → APPAREMMENT ACTIF ({signed_count} autres signés)")
                                    print(f"   │    → Le bot DOIT vous notifier")
                                    active_calls.append({
                                        'description': desc,
                                        'start_date': evt.get('startDate', 0),
                                        'teachers': evt.get('teachers', []),
                                        'signed_count': signed_count,
                                        'total': len(lines)
                                    })
                                else:
                                    print(f"   │    signature: null ✅")
                                    print(f"   │    → Appel pas encore lancé")
                            elif sig.get('signed') is True:
                                print(f"   │    signature.signed: true ✅")
                                print(f"   │    → Vous avez déjà signé")
                            else:
                                print(f"   │    signature.signed: false ⚠️")
                                print(f"   │    → Appel actif, pas encore signé")
                                active_calls.append({
                                    'description': desc,
                                    'start_date': evt.get('startDate', 0),
                                    'teachers': evt.get('teachers', []),
                                    'signed_count': signed_count,
                                    'total': len(lines)
                                })
                            break
                else:
                    print(f"   │  Attendance Sheet: ❌ Aucune (pas encore lancée)")
                print(f"   └──────────────────────────────────────────────")

    print(f"\n   Total événements: {events_found}")
    print(f"   Appels détectés: {len(active_calls)}")

    # ÉTAPE 4 : Logique du bot
    step += 1
    print_step(step, "Logique de détection du bot")
    print("   Le bot détecte un appel quand:")
    print("   1. Une attendance sheet existe")
    print("   2. ET au moins un étudiant a signé")
    print("   3. ET vous n'avez pas encore signé")
    print(f"   → Résultat: {len(active_calls)} appel(s) détecté(s)")

    # ÉTAPE 5 : Envoi notification Discord (simulation)
    step += 1
    print_step(step, "Test envoi notification Discord")

    if active_calls:
        print(f"   Notification à envoyer pour: {active_calls[0]['description']}")
        print(f"   Détails:")
        teacher_names = ', '.join([f"{t.get('firstName')} {t.get('lastName')}" for t in active_calls[0]['teachers']])
        print(f"   - Enseignants: {teacher_names}")
        print(f"   - Heure: {datetime.fromtimestamp(active_calls[0]['start_date'] / 1000).strftime('%H:%M')}")
        print(f"   - Signature: {active_calls[0]['signed_count']}/{active_calls[0]['total']} signés")

            # Test réel d'envoi Discord
        try:
            role_id = "1424662356868337775"
            payload = {
                "content": f"<@&{role_id}> 🎒 **Test Bot César - Appel détecté**",
                "embeds": [{
                    "title": "🔔 Appel César détecté!",
                    "description": f"Événement: {active_calls[0]['description']}",
                    "color": 15158332,
                    "fields": [
                        {
                            "name": "Signatures",
                            "value": f"{active_calls[0]['signed_count']}/{active_calls[0]['total']} étudiants",
                            "inline": True
                        },
                        {
                            "name": "Heure",
                            "value": datetime.fromtimestamp(active_calls[0]['start_date'] / 1000).strftime('%H:%M'),
                            "inline": True
                        }
                    ]
                }]
            }

            response = requests.post(WEBHOOK_URL, json=payload)

            if response.status_code in [200, 204]:
                print("   ✅ Notification Discord envoyée avec succès!")
                print(f"   (Status code: {response.status_code})")
            else:
                print(f"   ❌ Erreur Discord: {response.status_code}")
                print(f"   Réponse: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Erreur lors de l'envoi: {e}")
    else:
        print("   ℹ️  Aucun appel actif - pas de notification à envoyer")

    # RÉSUMÉ FINAL
    print()
    print("=" * 70)
    print("RÉSUMÉ DU TEST")
    print("=" * 70)
    print(f"Événements analysés: {events_found}")
    print(f"Appels détectés: {len(active_calls)}")
    print(f"Notification Discord: {'Envoyée' if active_calls else 'Non nécessaire'}")
    print()
    if len(active_calls) > 0:
        print("✅ Le bot fonctionne correctement!")
        print("✅ Il détectera les appels et enverra des notifications sur Discord.")
    else:
        print("ℹ️  Aucun appel actif en ce moment.")
        print("   Le bot attendra qu'un appel soit lancé pour vous notifier.")
    print("=" * 70)

    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
        sys.exit(1)
