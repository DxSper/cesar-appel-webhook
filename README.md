# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord et/ou Instagram.

## Fonctionnalités

- ✅ Détecte automatiquement quand un appel est lancé
- ✅ Vous notifie sur Discord et/ou Instagram
- ✅ Ne vous spam pas si vous avez déjà signé
- ✅ **Léger** : Mode cron (pas de processus permanent)
- ✅ Tout configurable via `.env`
- ✅ Support 2FA automatique

## Installation

```bash
git clone https://github.com/DxSper/cesar-appel-webhook.git
cd cesar-appel-webhook
pip3 install -r requirements.txt
cp .env.example .env
```

## Configuration

Éditez `.env` avec vos informations :

### Variables obligatoires

```env
CESAR_USERNAME=votre_identifiant
CESAR_PASSWORD=votre_mot_de_passe
```

### Notification Discord (optionnel)

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/VOTRE_WEBHOOK_ID/VOTRE_WEBHOOK_TOKEN
DISCORD_ROLE_ID=1234567890123456789
```

Pour créer un webhook Discord : Paramètres du serveur > Intégrations > Webhooks > Nouveau webhook.

### Notification Instagram (optionnel)

```env
INSTAGRAM_USERNAME=votre_username
INSTAGRAM_PASSWORD=votre_mot_de_passe
INSTAGRAM_THREAD_ID=1234567890123456
# Secret TOTP pour 2FA (optionnel)
INSTAGRAM_TOTP_SECRET=votre_secret_totp
```

**Pour trouver le Thread ID** : Ouvrez la conversation Instagram dans le navigateur > Regardez l'URL :
`https://www.instagram.com/direct/t/XXXXXXXXX/` → le nombre = Thread ID

**Pour le TOTP Secret** : Quand vous configurez l'authentification 2FA sur Instagram, sauvegardez le "secret" (format: `***REMOVED***`). Le bot générera automatiquement les codes.

### Horaires (optionnel)

```env
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

# Heure d'envoi du planning
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

## Structure

```
├── main.py
├── check_now.sh          # Script pour cron
├── .env.example          # Template config
├── requirements.txt
└── src/
    ├── cesar_client.py
    ├── discord_notifier.py
    ├── instagram_notifier.py
    ├── bot_loop.py
    └── diagnostics.py
```

## Dépannage

- `python3 main.py verify` - Vérifier la connexion César
- `tail -f bot.log` - Voir les logs
- Pour Instagram : le session cookie est sauvegardé dans `~/.cesar-bot/instagram_session.json`
- Si 2FA requis : vérifiez que `INSTAGRAM_TOTP_SECRET` est correct

## Licence

MIT
