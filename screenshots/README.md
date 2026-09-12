# Captures d'écran — preuves

Ce dossier contient les captures d'écran justifiant les vulnérabilités identifiées, leur
correction, et l'exécution du pipeline. Nommage suggéré (déjà l'ordre dans lequel elles ont
été prises pendant l'audit) :

## Contexte / application
- `01-juice-shop-home.png` — page d'accueil de l'application cible
- `02-jenkins-dashboard.png` — dashboard Jenkins initial

## Partie 1 — Identification des vulnérabilités (code + exploitation live)
- `v1-sqli-code.png` — `routes/login.ts:34`, requête SQL concaténée
- `v1-sqli-exploit.png` — connexion réussie via `' OR 1=1--`
- `v2-xss-exploit.png` — bandeau "DOM XSS" après injection du payload dans la recherche
- `v3-idor-code.png` — `routes/basket.ts`, absence de vérification de propriété
- `v3-idor-exploit-before.png` — `fetch('/rest/basket/2')` renvoyant le panier d'un autre utilisateur (bid réel = 1)
- `v4-secret-code.png` — `lib/insecurity.ts:21`, clé RSA en clair
- `v5-md5-code.png` — `lib/insecurity.ts:41`, hachage MD5
- `v6-deps-code.png` — `package.json`, versions vulnérables (`jsonwebtoken`, `express-jwt`, `sanitize-html`)

## Partie 3 — Vérification des remédiations
- `v1-sqli-fixed.png` — le même payload `' OR 1=1--` échoue désormais sur l'app reconstruite
- `v3-idor-fixed.png` — `fetch('/rest/basket/2')` renvoyant `403 Forbidden` après correction
- `pipeline-before-after-summary.png` — résumé Jenkins comparant les résultats avant/après

## Partie 4-5 — Pipeline Jenkins et résultats
- `jenkins-job-config.png` — configuration du job Pipeline
- `jenkins-stage-view.png` — vue des étapes du pipeline (build réussi)
- `jenkins-console-summary.png` — fin de la Console Output avec le résumé des outils
