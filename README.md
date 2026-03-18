# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord avec mention de rôle.

## Fonctionnalités

- ✅ **Appels** : Détecte automatiquement quand un appel est lancé et vous notifie sur Discord.
- ✅ **Emploi du temps** : Vous envoie le planning du jour tous les matins à 8h00 (mode daemon).
- ✅ **Intelligent** : Ne vous spamme pas si vous avez déjà signé.
- ✅ **Optimisé** : Se met en veille hors des heures de cours pour économiser les ressources.
- ✅ **Léger** : Mode cron disponible (pas de processus permanent).

## Installation

```bash
# Cloner le repo
git clone https://github.com/DxSper/cesar-appel-webhook.git
cd cesar-appel-webhook

# Installer les dépendances
pip3 install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditez le fichier .env avec vos informations
```

## Configuration (.env)

```env
# Identifiants César
CESAR_USERNAME=votre_identifiant
CESAR_PASSWORD=votre_mot_de_passe

# Webhook Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/VOTRE_WEBHOOK_ID/VOTRE_WEBHOOK_TOKEN

# ID du rôle Discord à mentionner
DISCORD_ROLE_ID=1234567890123456789
```

### Obtenir l'ID du rôle Discord

1. Activez le **Mode Développeur** dans Discord (Paramètres > Avancé > Mode Développeur)
2. Clic droit sur le rôle > **"Copier l'ID"**
3. Assurez-vous que le rôle est "Mentionnable par tout le monde".

## Utilisation (méthode recommandée : cron)

Le bot fonctionne par **sessions** : matin (9h13-13h43) et après-midi (13h43-17h15).

### 1. Rendre le script exécutable

```bash
chmod +x check_now.sh
```

### 2. Ajouter au crontab

```bash
crontab -e
```

### 3. Ajouter ces lignes

```cron
# Session matin : lance à 9h13, vérifie toutes les 30s jusqu'à 13h43
13 9 * * 1-5 /home/USERNAME/cesar-appel-webhook/check_now.sh morning

# Session après-midi : lance à 13h43, vérifie toutes les 30s jusqu'à 17h15
43 13 * * 1-5 /home/USERNAME/cesar-appel-webhook/check_now.sh afternoon
```

**⚠️** Remplacez `/home/USERNAME/cesar-appel-webhook` par votre chemin.

### Comment ça marche

| Cron lance à | Session | Vérifie | S'arrête à |
|---------------|---------|---------|------------|
| 9h13 | Matin | Toutes les 30s | 13h43 |
| 13h43 | Après-midi | Toutes les 30s | 17h15 |

- Si **pas de cours aujourd'hui** → le bot quitte immédiatement (pas de checks inutiles)
- Pas de processus la **nuit**

### Test manuel

```bash
./check_now.sh morning   # Session matin
./check_now.sh afternoon # Session après-midi
```

## Alternative : Mode daemon (processus permanent)

Si vous préférez un processus qui tourne en continu :

```bash
python3 main.py run
```

Options :
- `--start-hour 9 --start-minute 13` : Début session matin
- `--afternoon-hour 13 --afternoon-minute 43` : Début session après-midi
- `--schedule-hour 8 --schedule-minute 0` : Envoi du planning à 8h
- `--check-interval 60` : Intervalle entre chaque vérification

### Mode écoute continue

Surveillance agressive sans mise en veille :
```bash
python3 main.py listen
```

### Vérification rapide

```bash
python3 main.py verify   # Vérifie l'état sans notification
python3 main.py test     # Vérifie et notifie si appel actif
```

## Détection des appels

Le bot notifie quand :
1. ✅ Une feuille d'émargement existe
2. ✅ Vous n'avez pas encore signé
3. ✅ D'autres étudiants ont signé OU la feuille est clôturée par le prof

## Structure du projet

```text
cesar-appel-webhook/
├── main.py                  # Point d'entrée CLI
├── check_now.sh            # Script pour cron (sessions)
├── run_bot.sh              # Script pour daemon
├── requirements.txt
├── cesar-bot.service.example
└── src/
    ├── cesar_client.py       # Connexion César
    ├── discord_notifier.py   # Notifications Discord
    ├── bot_loop.py          # Boucles de surveillance
    └── diagnostics.py       # Tests
```

## Service systemd (optionnel)

```bash
sudo cp cesar-bot.service.example /etc/systemd/system/cesar-bot.service
sudo nano /etc/systemd/system/cesar-bot.service  # Remplacez USERNAME
sudo systemctl daemon-reload
sudo systemctl enable cesar-bot
sudo systemctl start cesar-bot
```

## Dépannage

- **Erreur de connexion** : Vérifiez `.env`. Testez : `python3 main.py verify`
- **Pas de notification** : Lancez `verify`. Si aucun étudiant n'a signé, le bot ne notifie pas.
- **Cron ne marche pas** : `chmod +x check_now.sh`, testez manuellement `./check_now.sh morning`

## Licence

MIT
