# César Attendance Call Bot 🎒

Un bot léger qui surveille l'application César pour détecter les appels de présence et vous notifier via Discord avec mention de rôle.

## Fonctionnalités

- ✅ Détecte automatiquement quand un appel est lancé (quand signingOff=true)
- ✅ Vous notifie sur Discord dès que la feuille d'émargement est ouverte
- ✅ Vous notifie sur Discord uniquement si vous n'avez pas encore signé
- ✅ Ne vous spam pas si vous avez déjà signé
- ✅ **Léger** : cron lance le bot par session, pas de processus permanent la nuit

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

## Lancement automatique avec cron

Le bot fonctionne par **sessions** : une le matin (9h13-13h43), une l'après-midi (13h43-18h).

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
# Session matin : 9h13 → vérifie toutes les 30s jusqu'à 13h43
13 9 * * 1-5 /home/USERNAME/cesar_ping/check_now.sh morning

# Session après-midi : 13h43 → vérifie toutes les 30s jusqu'à 18h
43 13 * * 1-5 /home/USERNAME/cesar_ping/check_now.sh afternoon
```

**⚠️ Important** : Remplacez `/home/USERNAME/cesar_ping` par le chemin où vous avez cloné le repo.

### Comment ça marche

| Cron lance à | Session | Bot vérifie | Bot s'arrête à |
|---------------|---------|-------------|----------------|
| 9h13 | Matin | Toutes les 30s | 13h43 |
| 13h43 | Après-midi | Toutes les 30s | 18h00 |

Le bot dort entre chaque check (30s) et quitte automatiquement à la fin de la session. Pas de processus la nuit !

### Test manuel

```bash
# Tester la session matin
./check_now.sh morning

# Tester la session après-midi
./check_now.sh afternoon

# Voir les logs
tail -f bot.log
```

## Alternative : Mode service systemd

Si vous préférez un processus permanent :

```bash
cp cesar-bot.service.example /etc/systemd/system/cesar-bot.service
sudo nano /etc/systemd/system/cesar-bot.service
# Remplacez USERNAME par votre nom d'utilisateur
sudo systemctl daemon-reload
sudo systemctl enable cesar-bot
sudo systemctl start cesar-bot
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
├── bot.py              # Bot principal
├── check_now.sh        # Script pour cron (lance une session)
├── listen_now.py       # Script de surveillance continue (alternative)
├── verify.py           # Vérification rapide
├── test_complet.py     # Test détaillé
├── test_bot.py         # Test de détection
├── run_bot.sh          # Script pour mode systemd
├── cesar-bot.service.example  # Template systemd
├── .env.example        # Template configuration
├── requirements.txt    # Dépendances Python
└── README.md           # Ce fichier
```

## Vérification rapide

```bash
# Voir l'état actuel
python3 verify.py
```

## Dépannage

### Pas de notification ?
- Vérifiez les logs : `tail -f bot.log`
- Vérifiez votre webhook Discord
- Lancez `python3 verify.py` pour voir l'état actuel

### Erreur de connexion ?
- Vérifiez vos identifiants César dans `.env`

### Cron ne marche pas ?
- Vérifiez que le script est exécutable : `chmod +x check_now.sh`
- Vérifiez les logs cron : `grep CRON /var/log/syslog` (ou `journalctl -u cron`)
- Testez manuellement : `./check_now.sh morning`

## Licence

MIT - Libre d'utilisation et de modification.
