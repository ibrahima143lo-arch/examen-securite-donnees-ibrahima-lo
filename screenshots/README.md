# Captures d'écran — preuves

Ce dossier contient les captures d'écran justifiant les vulnérabilités identifiées, leur
correction, et l'exécution du pipeline. Nommage suggéré (déjà l'ordre dans lequel elles ont
été prises pendant l'audit) :

## Contexte / application
- `01-juice-shop-home.png` — page d'accueil de l'application cible
- `02-jenkins-dashboard.png` — dashboard Jenkins initial

## Partie 1 — Identification des vulnérabilités (code + exploitation live)
- `v1-sqli-code.png` — `remediation/before/login.ts.orig`, requête SQL concaténée (version vulnérable d'origine)
- `v2-xss-exploit.png` — bandeau "DOM XSS" après injection du payload dans la recherche
- `v3-idor-code.png` — `remediation/before/basket.ts.orig`, absence de vérification de propriété (version vulnérable d'origine)
- `v4-secret-code.png` — `remediation/before/insecurity.ts.orig`, clé RSA en clair (version vulnérable d'origine)
- `v5-md5-code.png` — `lib/insecurity.ts:41`, hachage MD5 (toujours présent, non corrigé)
- `v6-deps-code.png` — `package.json`, versions vulnérables (`jsonwebtoken`, `express-jwt`, `sanitize-html`)

> Note : `v1-sqli-exploit.png` (bypass réussi) et `v3-idor-exploit-before.png` (lecture du panier
> d'un autre utilisateur) n'ont pas été repris après la perte accidentelle des premières
> captures, car l'application de démonstration tourne désormais avec le code **corrigé** — les
> reproduire aurait exigé de reconstruire une version volontairement non patchée. Le code
> vulnérable d'origine (ci-dessus, dossier `remediation/before/`) et la preuve que l'attaque
> échoue après correction (`v1-sqli-fixed.png`, `v3-idor-fixed.png`, ci-dessous) sont jugés
> suffisants pour justifier V1 et V3.

## Partie 3 — Vérification des remédiations
- `v1-sqli-fixed.png` — le même payload `' OR 1=1--` échoue désormais sur l'app reconstruite
- `v3-idor-fixed.png` — `fetch('/rest/basket/2')` renvoyant `403 Forbidden` après correction

> `pipeline-before-after-summary.png` a été fusionnée avec `jenkins-console-summary.png`
> ci-dessous (même contenu : le résumé Jenkins avant/après).

## Partie 4-5 — Pipeline Jenkins et résultats
- `jenkins-job-config.png` — configuration du job Pipeline
- `jenkins-stage-view.png` — vue des étapes du pipeline (build réussi)
- `jenkins-console-summary.png` — fin de la Console Output avec le résumé des outils
