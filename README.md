# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord avec mention de rôle.

## Fonctionnalités

- ✅ Détecte automatiquement quand un appel est lancé
- ✅ Vous notifie sur Discord
- ✅ Ne vous spam pas si vous avez déjà signé
- ✅ **Léger** : Mode cron (pas de processus permanent)
- ✅ Tout configurable via `.env`

## Installation

```bash
git clone https://github.com/DxSper/cesar-appel-webhook.git
cd cesar-appel-webhook
pip3 install -r requirements.txt
cp .env.example .env
```

## Configuration

Éditez `.env` avec vos informations :

```env
# === REQUIRED ===
CESAR_USERNAME=votre_identifiant
CESAR_PASSWORD=votre_mot_de_passe
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# === OPTIONAL (defaults shown) ===
DISCORD_ROLE_ID=1234567890123456789

# Session matin (9:13 - 13:43)
BOT_START_HOUR=9
BOT_START_MINUTE=13
BOT_END_HOUR=13
BOT_END_MINUTE=43

# Session après-midi (13:43 - 17:15)
BOT_AFTERNOON_START_HOUR=13
BOT_AFTERNOON_START_MINUTE=43
BOT_AFTERNOON_END_HOUR=17
BOT_AFTERNOON_END_MINUTE=15

# Intervalle entre chaque vérification (secondes)
BOT_CHECK_INTERVAL=30

# Heure d'envoi du planning (mode daemon)
SCHEDULE_HOUR=8
SCHEDULE_MINUTE=0
```

## Lancement

### Méthode recommandée : cron

```bash
chmod +x check_now.sh
```

Ajouter au crontab (`crontab -e`) :

```cron
# Envoi du planning (8h00, lun-ven)
0 8 * * 1-5 /home/USER/cesar-appel-webhook/check_now.sh schedule

# Session matin - vérification appel (9h13, lun-ven)
13 9 * * 1-5 /home/USER/cesar-appel-webhook/check_now.sh morning

# Session après-midi - vérification appel (13h43, lun-ven)
43 13 * * 1-5 /home/USER/cesar-appel-webhook/check_now.sh afternoon
```

**Note :** `1-5` = lundi à vendredi (le bot ne se lance pas le weekend)

### Commandes CLI

```bash
python3 main.py session schedule  # Envoi planning puis quitte
python3 main.py session morning   # Check appel matin puis quitte
python3 main.py session afternoon # Check appel après-midi puis quitte
python3 main.py listen           # Écoute continue (pour tester)
python3 main.py verify           # Vérifier l'état
python3 main.py test             # Test avec notification
```

**Note :** Pour une utilisation normale, utilisez `check_now.sh` avec cron (voir ci-dessus).

## Structure

```
├── main.py
├── check_now.sh          # Pour cron
├── .env.example         # Template config
└── src/
    ├── cesar_client.py
    ├── discord_notifier.py
    ├── bot_loop.py
    └── diagnostics.py
```

## Dépannage

- `python3 main.py verify` pour diagnostiquer
- `tail -f bot.log` pour voir les logs

## Licence

MIT
