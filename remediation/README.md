# Remédiations appliquées

Trois vulnérabilités critiques ont été corrigées directement dans le code source de
l'application (`../juice-shop`). Pour chacune : cause, correction, justification et
méthode de vérification.

---

## 1. SQL Injection — `routes/login.ts` (CWE-89)

**Fichier / avant** : [`before/login.ts.orig`](before/login.ts.orig)
**Fichier / après** : voir `juice-shop/routes/login.ts` (patché en place)

### Cause
La requête d'authentification est construite par concaténation de chaînes : les valeurs
`req.body.email` et `req.body.password` (hash) sont directement interpolées dans un
template literal SQL exécuté via `sequelize.query(...)`. Aucune séparation entre code SQL
et données utilisateur → une entrée telle que `' OR 1=1--` modifie la logique de la requête
(contournement d'authentification).

### Correction
Remplacement de l'interpolation par une requête **paramétrée**, en utilisant le mécanisme
`replacements` de Sequelize (liaison de variables `:email` / `:password` au lieu de
concaténation) :

```ts
models.sequelize.query(
  'SELECT * FROM Users WHERE email = :email AND password = :password AND deletedAt IS NULL',
  {
    model: UserModel,
    plain: true,
    replacements: {
      email: req.body.email || '',
      password: security.hash(req.body.password || '')
    }
  }
)
```

### Justification
Avec des requêtes paramétrées, le moteur SQL traite les valeurs fournies uniquement comme
des **données**, jamais comme du code SQL exécutable — la classe de vulnérabilité CWE-89 est
éliminée par construction, indépendamment de la qualité de la validation d'entrée en amont
(défense en profondeur).

### Vérification
- **Test manuel** : rejouer le payload `admin@juice-sh.op' --` / mot de passe vide → réponse
  `401 Invalid email or password` au lieu d'une connexion réussie (voir
  `remediation/verification/sqli-test.md`).
- **Outil** : re-scan Semgrep (règle `javascript.sequelize.security.sequelize-injection`,
  jeu de règles `p/owasp-top-ten`) → 0 finding sur `routes/login.ts` après correction
  (voir `reports/semgrep-report-after.json` vs `reports/semgrep-report.json`).

---

## 2. Broken Access Control / IDOR — `routes/basket.ts` (CWE-639)

### Cause
`retrieveBasket` récupère un panier uniquement à partir de `req.params.id` (fourni par le
client dans l'URL), sans jamais vérifier que ce panier appartient bien à l'utilisateur
authentifié de la requête. Le seul contrôle existant (`challengeUtils.solveIf(...)`) sert à
détecter l'exploitation à des fins de scoring interne, pas à la bloquer.

### Correction
Ajout d'un contrôle d'autorisation explicite avant l'accès aux données : l'identifiant de
panier demandé doit correspondre au `bid` associé au token de l'utilisateur authentifié,
sinon la requête est rejetée avec `403 Forbidden`.

```ts
const id = req.params.id
const user = security.authenticatedUsers.from(req)
if (user == null || String(user.bid) !== String(id)) {
  res.status(403).json({ error: 'Access to this basket is not permitted.' })
  return
}
const basket = await BasketModel.findOne({ where: { id }, include: [...] })
```

### Justification
Le contrôle d'accès est désormais appliqué **côté serveur**, sur une donnée que le client
ne peut pas falsifier (le `bid` est lié au token JWT signé émis à la connexion), conforme au
principe : ne jamais faire confiance à un identifiant fourni par le client sans vérifier les
droits d'accès associés (OWASP A01:2021 - Broken Access Control).

### Vérification
- **Test manuel** : utilisateur A se connecte, note son `bid` (ex. 5) ; requête
  `GET /rest/basket/6` (panier de l'utilisateur B) avec le token de A → `403` au lieu du
  contenu du panier de B (voir `remediation/verification/idor-test.md`).
- **Outil** : re-scan DAST OWASP ZAP → l'alerte liée à l'énumération d'IDs consécutifs sur
  `/rest/basket/{id}` n'est plus remontée / passe en information faible.

---

## 3. Hardcoded secret — clé privée RSA JWT — `lib/insecurity.ts` (CWE-798)

### Cause
La clé privée RSA utilisée pour signer tous les tokens JWT d'authentification
(`jwt.sign(user, privateKey, { algorithm: 'RS256' })`) est codée en dur directement dans le
code source, versionnée dans le dépôt Git. Toute personne ayant accès au code source (dépôt
public/privé compromis, ancien commit, fork) peut forger des tokens valides pour
n'importe quel utilisateur, y compris un administrateur.

### Correction
1. Génération d'une nouvelle paire de clés RSA (`openssl genrsa` / `openssl rsa -pubout`),
   qui **remplace** l'ancienne paire potentiellement compromise (rotation du secret).
2. La clé privée est déplacée dans un fichier `encryptionkeys/jwt.key`, **exclu du dépôt Git**
   (`.gitignore`), et chargée au démarrage :

```ts
const privateKey = fs
  ? fs.readFileSync('encryptionkeys/jwt.key', 'utf8')
  : 'placeholder-private-key'
```

3. En production, ce fichier serait fourni via un secret manager (Docker secret, Vault,
   variable d'environnement injectée par la plateforme) plutôt que copié dans l'image.

### Justification
Séparer le secret du code source empêche sa divulgation par simple lecture du dépôt
(historique Git inclus) et permet une rotation du secret sans modifier le code. C'est la
correction standard recommandée pour CWE-798 (Use of Hard-Coded Credentials).

### Vérification
- **Outil** : re-scan Gitleaks sur `lib/insecurity.ts` → 0 secret détecté après correction
  (le fichier `jwt.key` n'est ni commité ni scanné dans le dépôt).
- **Test manuel** : un ancien token signé avec l'ancienne clé privée (avant rotation) est
  rejeté par `isAuthorized()` car il ne correspond plus à la nouvelle clé publique
  `encryptionkeys/jwt.pub` → invalidation effective des tokens potentiellement compromis.

---

## Note sur les vulnérabilités non corrigées dans ce dépôt

Les vulnérabilités V2 (XSS), V5 (hash MD5) et V6 (dépendances obsolètes) sont documentées
dans le rapport (description, CWE, impact CIA, remédiation proposée) mais n'ont pas été
patchées dans le code de démonstration, conformément au minimum de 3 corrections demandé par
l'énoncé. Leur correction suit le même principe (encodage de sortie contextuel pour la XSS,
`bcrypt`/`argon2` avec sel pour le hachage, mise à jour de version + `npm audit fix` pour les
dépendances).
