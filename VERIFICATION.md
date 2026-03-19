# Vérification du Bot César

## Test du 18 mars 2026

### État actuel détecté :

**Événement 1: Campus SDV (matin)**
- Heure: 09:15 - 12:45
- Attendance Sheet: **Existe** (`019d0028-76dc-77dd-a806-36eb0b6d2815`)
- Étudiants: 44
- **MON ÉTAT:**
  - signingOff: `true` ✓
  - attendanceWithoutSignature: `false`
  - signature: `null`

**Événement 2: Campus SDV - Conférences (après-midi)**
- Heure: 13:45 - 17:15
- Attendance Sheet: **Aucune** (pas encore créée)

---

## Logique de détection actuelle

Le bot détecte un appel quand :

| Condition | Résultat |
|-----------|----------|
| Attendance sheet existe + signingOff=true + signature=null | ✅ DETECTÉ |
| Attendance sheet existe + signature existe + signed=false | ✅ DETECTÉ |
| Attendance sheet existe + signature existe + signed=true | ❌ Déjà signé |

---

## Problème identifié

Le bot détecte l'événement "Campus SDV" comme un appel d'urgence alors que :
1. L'appel n'est pas nécessairement **ouvert** aux signatures
2. `signingOff=true` + `signature=null` pourrait signifier "appel préparé" pas "appel actif"

### Questions à résoudre :

1. **Quand l'appel est-il VRAIMENT lancé ?**
   - Est-ce quand `signingOff` passe à `true` ?
   - Ou quand une signature avec `signed=false` apparaît ?

2. **Comment l'utilisateur peut-il signer ?**
   - Via une interface web sur César ?
   - Via une API ? (à trouver)

---

## Recommandation

### Option 1 : Attente de l'apparition d'une signature
- Ne notifier que si une signature avec `signed=false` apparaît
- Problème : `signature` est `null` même quand l'appel est "préparé"

### Option 2 : Utiliser `signingOff` comme indicateur
- Notifier quand `signingOff=true` ET `signature=null`
- C'est ce que le bot fait actuellement

### Option 3 : Vérifier le statut de l'attendance sheet
- Chercher un champ `status` ou `state` dans l'attendance sheet
- Voir si l'appel est "open", "closed", "pending", etc.

---

## Action à prendre

Je vais créer un script pour **simuler l'appel** et vérifier comment le site réagit quand un appel est réellement lancé.

En attendant, voici ce que vous pouvez faire :

1. **Lancer le bot** et voir quelles notifications arrivent
2. **Vérifier les logs** pour voir quand il détecte les appels
3. **Tester manuellement** sur César quand un appel est lancé

---

## Commandes de test

### Lancer le test complet
```bash
python3 test_bot.py
```

### Lancer le bot avec logs détaillés
```bash
python3 bot.py --webhook "YOUR_WEBHOOK" --check-interval 30
```

### Voir les logs en temps réel
```bash
tail -f bot.log
```
