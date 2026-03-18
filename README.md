# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord avec mention de rôle.

## Fonctionnalités

- ✅ Détecte automatiquement quand un appel est lancé (quand signingOff=true)
- ✅ Vous notifie sur Discord dès que la feuille d'émargement est ouverte
- ✅ Vous notifie sur Discord uniquement si vous n'avez pas encore signé
- ✅ Ne vous spam pas si vous avez déjà signé
- ✅ Se réveille automatiquement pendant les heures de cours

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

### Mode surveillance continue (recommandé)

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

## Comment ça fonctionne

### Logique de détection des signatures

Le bot envoie une notification Discord quand :

1. ✅ Une feuille d'émargement existe pour l'événement
2. ✅ Vous n'avez pas encore signé (votre signature est null ou signed=false)
3. ✅ Soit l'appel est préparé (`signingOff=true`, signatures en attente), soit au moins un étudiant a signé

Le bot **ne vous notifie pas** si vous avez déjà signé (`signed=true`).

### États possibles

| État | Feuille | signingOff | Étudiants signés | Votre signature | Action |
|------|---------|------------|------------------|-----------------|--------|
| Appel préparé | Existe | true | 0 | null | ✅ **Notifier !** |
| Appel actif | Existe | true | > 0 | null | ✅ **Notifier !** |
| Appel actif, pas signé | Existe | true | > 0 | signed=false | ✅ **Notifier !** |
| Déjà signé | Existe | true | > 0 | signed=true | ❌ Ne rien faire |

### Exemple concret

**Cas 1 : Appel préparé (personne n'a encore signé)**
```
Événement: Campus SDV
- Heure: 09:15 - 12:45
- Étudiants: 44
- Signatures: 0/44
- signingOff: true

→ Votre état: signature = null
→ Appel préparé, en attente de signatures
→ ✅ Le bot vous notifie sur Discord
```

**Cas 2 : Appel actif (des étudiants ont signé)**
```
Événement: Campus SDV
- Heure: 09:15 - 12:45
- Étudiants: 44
- Signatures: 11/44

→ Votre état: signature = null (pas encore signé)
→ ✅ Le bot vous notifie sur Discord
```

## Exemple de notification Discord

```
@ROLE 🎒 Appel César disponible

🔔 Appel détecté sur César!
Une feuille d'émargement est disponible pour:
**Campus SDV - Conférences**

Type: Séance de cours | Heure: 13:45
Enseignant(s): Christophe HERROU
Signatures: 11/44 étudiants ont signé
```

## Structure du projet

```
├── bot.py              # Bot principal avec scheduling
├── listen_now.py       # Script de surveillance continue
├── verify.py          # Vérification rapide
├── test_complet.py    # Test détaillé
├── test_bot.py        # Test de détection
├── run_bot.sh         # Script de lancement
├── cesar-bot.service.example  # Template systemd (à adapter)
├── .env.example       # Template configuration
├── requirements.txt   # Dépendances Python
└── README.md          # Ce fichier
```

## Installation du service (optionnel)

Pour faire tourner le bot en arrière-plan avec systemd :

```bash
# Copier et adapter la configuration
cp cesar-bot.service.example /etc/systemd/system/cesar-bot.service

# Éditer avec vos chemins
sudo nano /etc/systemd/system/cesar-bot.service
# Remplacer USERNAME par votre nom d'utilisateur
# Remplacer /home/USERNAME/cesar_ping par le chemin du repo

sudo systemctl daemon-reload
sudo systemctl enable cesar-bot
sudo systemctl start cesar-bot
```

## Dépannage

### Pas de notification ?
- Vérifiez les logs : `tail -f bot.log`
- Vérifiez votre webhook Discord
- Lancez `python3 verify.py` pour voir l'état actuel

### Erreur de connexion ?
- Vérifiez vos identifiants César dans `.env`

## Licence

MIT - Libre d'utilisation et de modification.
