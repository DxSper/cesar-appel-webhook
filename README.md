# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord avec mention de rôle.

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
3. Cliquez sur **"Copier l'ID"**

## Lancement

### Mode surveillance continue (recommandé pour l'après-midi)

```bash
python3 listen_now.py
```

### Mode bot complet (avec scheduling)

```bash
python3 bot.py --webhook "$DISCORD_WEBHOOK_URL"
```

### Vérification rapide

```bash
python3 verify.py
```

## Fonctionnement

1. **Connexion** : Se connecte automatiquement à César avec vos identifiants
2. **Surveillance** : Vérifie toutes les 30 secondes si un appel est lancé
3. **Détection** : Détecte quand au moins un étudiant a signé et que vous n'avez pas encore signé
4. **Notification** : Envoie un message Discord avec mention du rôle

## Exemple de notification Discord

```
@ROLE 🎒 Appel César disponible

🔔 Appel détecté sur César!
Une feuille d'émargement est disponible pour:
**Campus SDV - Conférences**

Type: Séance de cours | Heure: 13:45
Enseignant(s): Christophe HERROU
```

## Structure du projet

```
├── bot.py              # Bot principal avec scheduling
├── listen_now.py       # Script de surveillance continue
├── verify.py          # Vérification rapide
├── test_complet.py    # Test détaillé
├── run_bot.sh         # Script de lancement
├── .env.example       # Template configuration
├── requirements.txt   # Dépendances Python
└── README.md          # Ce fichier
```

## Licence

MIT - Libre d'utilisation et de modification.
