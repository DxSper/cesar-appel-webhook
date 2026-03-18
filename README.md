# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord avec mention de rôle. Il vous envoie aussi votre emploi du temps chaque matin à 8h00.

## Fonctionnalités

- ✅ **Appels** : Détecte automatiquement quand un appel est lancé et vous notifie sur Discord.
- ✅ **Emploi du temps** : Vous envoie le planning du jour tous les matins à 8h00.
- ✅ **Intelligent** : Ne vous spamme pas si vous avez déjà signé.
- ✅ **Optimisé** : Se met en veille hors des heures de cours pour économiser les ressources.

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

Modifiez le fichier `.env` avec vos informations :

```env
# Identifiants César
CESAR_USERNAME=votre_identifiant
CESAR_PASSWORD=votre_mot_de_passe

# Webhook Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/VOTRE_WEBHOOK_ID/VOTRE_WEBHOOK_TOKEN

# ID du rôle Discord à mentionner
DISCORD_ROLE_ID=1234567890123456789
```

### Comment obtenir l'ID du rôle Discord

1. Activez le **Mode Développeur** dans Discord (Paramètres > Avancé > Mode Développeur)
2. Faites un **clic droit** sur le rôle à mentionner
3. Cliquez sur **"Copier l'ID"** (Attention : copiez bien l'ID d'un Rôle et non d'un Utilisateur)
4. Assurez-vous que le rôle est "Mentionnable par tout le monde" dans les paramètres du serveur.

## Utilisation (CLI)

Le bot se contrôle désormais via un point d'entrée unique `main.py` qui regroupe plusieurs commandes :

### 1. Mode normal (Recommandé pour serveur)
Gère la surveillance classique (mise en veille la nuit et le midi) et l'envoi du planning à 8h00.
```bash
python3 main.py run
```
*Note : Vous pouvez modifier l'heure de l'envoi du planning avec `--schedule-hour` et `--schedule-minute`.*

### 2. Mode écoute continue
Surveillance agressive toutes les 30 secondes sans aucune mise en veille.
```bash
python3 main.py listen
```

### 3. Vérification rapide
Vérifie l'état de la connexion et les appels en cours en console sans envoyer de notification Discord.
```bash
python3 main.py verify
```

### 4. Test complet
Fait une vérification complète et tente d'envoyer une notification Discord si un appel est actif.
```bash
python3 main.py test
```

## Fonctionnement de la détection

Le bot envoie une notification Discord quand :
1. ✅ Une feuille d'émargement existe.
2. ✅ Vous n'avez pas encore signé (votre signature est null ou signed=false).
3. ✅ D'autres étudiants ont déjà commencé à signer OU la feuille est marquée comme clôturée par le prof pour signature.

## Structure du projet

```text
cesar-appel-webhook/
├── .env                # Vos identifiants (ignoré par git)
├── .env.example        # Template de configuration
├── main.py             # Point d'entrée principal (CLI)
├── requirements.txt    # Dépendances Python
├── run_bot.sh          # Script de lancement pour les services
├── cesar-bot.service.example  # Template systemd
└── src/                # Code source modulaire
    ├── cesar_client.py     # Logique de connexion et scraping César
    ├── discord_notifier.py # Logique d'envoi des embeds Discord
    ├── bot_loop.py         # Boucles de surveillance (run / listen)
    └── diagnostics.py      # Scripts de test et vérification
```

## Installation en service (Arrière-plan permanent)

Pour faire tourner le bot en arrière-plan avec systemd sur un serveur Linux :

```bash
# Copier et adapter la configuration
sudo cp cesar-bot.service.example /etc/systemd/system/cesar-bot.service

# Éditer le fichier avec vos chemins (Remplacez USERNAME)
sudo nano /etc/systemd/system/cesar-bot.service

sudo systemctl daemon-reload
sudo systemctl enable cesar-bot
sudo systemctl start cesar-bot
```

## Dépannage

- **Erreur de connexion** : Vérifiez vos identifiants dans `.env`. S'ils sont corrects, utilisez `python3 main.py verify` pour diagnostiquer.
- **Rôle Inconnu sur Discord** : Assurez-vous que l'ID dans `.env` est bien un rôle et non un utilisateur.
- **Pas de notification** : Lancez `python3 main.py verify`. S'il n'y a **aucun étudiant signé** et que le prof n'a pas cloturé la feuille, le bot ne notifie pas (pour éviter les faux positifs).

## Licence

MIT - Libre d'utilisation et de modification.
