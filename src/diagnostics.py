import sys
from datetime import datetime

from .cesar_client import CesarClient

def print_step(step, message, status=""):
    print(f"{step:2d}. {message} {status}")

def run_verify(username, password):
    """Corresponds to old verify.py logic: Check if login works and print active calls."""
    print("=" * 60)
    print("VÉRIFICATION RAPIDE DU BOT CÉSAR")
    print("=" * 60)
    print()

    client = CesarClient(username, password)
    
    print("1. Connexion à César...")
    if client.login():
        print(f"   ✅ Connexion réussie (UUID: {client.student_uuid})")
    else:
        print("   ❌ Échec de connexion")
        return False
        
    print("\n2. Analyse des événements du jour...")
    events = client.get_raw_events()
    active_calls = client.extract_active_calls(events)
    
    for evt in events:
        start_ts = evt.get('startDate', 0) / 1000
        end_ts = evt.get('endDate', 0) / 1000
        desc = evt.get('description', 'Inconnu')
        
        print(f"\n   Événement: {desc}")
        print(f"   Début: {datetime.fromtimestamp(start_ts) if start_ts else 'N/A'}")
        print(f"   Fin: {datetime.fromtimestamp(end_ts) if end_ts else 'N/A'}")
        
    print()
    print(f"   → Total événements: {len(events)}")
    print(f"   → Appels détectés qui nécessitent signature: {len(active_calls)}")
    
    print("\n" + "=" * 60)
    if len(active_calls) > 0:
        print("✅ RÉSULTAT: Des appels sont détectés, le bot fonctionnerait !")
    else:
        print("ℹ️  RÉSULTAT: Aucun appel actif détecté (normal selon l'heure)")
    print("=" * 60)
    
    return True

def run_full_test(username, password, webhook_url, role_id):
    """Corresponds to old test_complet.py: Verbose testing including actual Discord webhook ping."""
    print("=" * 70)
    print("TEST COMPLET ET DÉTAILLÉ DU BOT CÉSAR")
    print("=" * 70)
    print()

    client = CesarClient(username, password)
    step = 1
    
    print_step(step, "Connexion à César")
    if client.login():
        print(f"   ✅ Connexion réussie (UUID: {client.student_uuid})")
    else:
        print("   ❌ Échec de connexion")
        return False
        
    step += 1
    print_step(step, "Analyse des événements du jour")
    events = client.get_raw_events()
    active_calls = client.extract_active_calls(events)
    
    print(f"\n   Total événements: {len(events)}")
    print(f"   Appels détectés: {len(active_calls)}")
    
    step += 1
    print_step(step, "Test envoi notification Discord")
    
    if active_calls:
        print(f"   Notification à envoyer pour: {active_calls[0]['description']}")
        
        from .discord_notifier import DiscordNotifier
        notifier = DiscordNotifier(webhook_url, role_id)
        
        try:
            if notifier.send_attendance_alert(active_calls[0]):
                print("   ✅ Notification Discord envoyée avec succès!")
            else:
                print("   ❌ Erreur d'envoi Discord")
        except Exception as e:
            print(f"   ❌ Erreur lors de l'envoi: {e}")
    else:
        print("   ℹ️  Aucun appel actif - pas de notification test à envoyer")
        
    print("\n" + "=" * 70)
    print("RÉSUMÉ DU TEST")
    print("=" * 70)
    print(f"Appels détectés: {len(active_calls)}")
    if len(active_calls) > 0:
        print("✅ Le bot fonctionne correctement!")
    else:
        print("ℹ️  Aucun appel actif en ce moment.")
    print("=" * 70)
    
    return True
