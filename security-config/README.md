# Configuration des outils de sécurité

Ce projet utilise volontairement les jeux de règles **par défaut** de chaque outil, sans
configuration personnalisée, afin de représenter un pipeline DevSecOps de base réaliste pour
une première mise en place :

| Outil | Configuration utilisée |
|---|---|
| Semgrep | Registries publics `p/owasp-top-ten`, `p/javascript`, `p/typescript` (voir `Jenkinsfile`) |
| Trivy | Scan `fs` par défaut, scanner `vuln` uniquement |
| Gitleaks | Détection par défaut (`gitleaks detect`), aucune règle custom ni allowlist |
| OWASP ZAP | `zap-baseline.py` (scan non intrusif), spider limité à 2 minutes |

## Pourquoi aucune configuration personnalisée ici

Une vraie mise en production ajouterait probablement :
- une **allowlist Gitleaks** pour les faux positifs propres à Juice Shop (données de
  challenge/test volontairement "secret-like") ;
- un **fichier de règles ZAP** (`-c`/`-n`) pour ignorer certaines alertes déjà acceptées par
  l'équipe sécurité ;
- des **règles Semgrep** supplémentaires ciblant les patterns spécifiques au projet.

Ce choix est discuté en Partie 6 du rapport (`reports/analyse-critique.md`) : l'absence de
tuning ici illustre justement pourquoi un outil "silencieux" par défaut ne garantit rien —
les faux positifs (ex. les ~66 alertes Gitleaks restantes, essentiellement des données de
test) doivent être triés manuellement plutôt que masqués aveuglément.
