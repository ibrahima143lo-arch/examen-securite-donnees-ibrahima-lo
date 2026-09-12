# Examen Final — Sécurité des données

Audit de sécurité, remédiation et pipeline CI/CD sécurisé pour **OWASP Juice Shop**,
utilisé comme application cible volontairement vulnérable.

## Structure du dépôt

```
project/
│
├── README.md                 # ce fichier
├── Jenkinsfile                # pipeline CI/CD (Checkout → Build → Security Analysis → DAST → Report → Notification)
├── docker-compose.yml         # orchestration Juice Shop + Jenkins (Docker Desktop)
├── juice-shop/                # code source de l'application cible (copie locale, patchée pour la remédiation)
├── jenkins/Dockerfile         # image Jenkins avec Semgrep, Trivy, Gitleaks, Docker CLI
├── scripts/aggregate_report.py# agrégation des rapports d'outils -> reports/summary.md
├── reports/                   # rapports (outils + rapport-securite.md/.pdf/.docx + scripts de génération)
├── screenshots/                # captures d'écran (app, Jenkins, résultats)
└── remediation/                # avant/après des correctifs appliqués
```

## Prérequis

- Docker Desktop (avec le backend WSL2 activé)
- Git

## Exécuter le projet en local

Depuis la racine du dépôt :

```bash
docker compose build
docker compose up -d
```

- Application cible (Juice Shop) : http://localhost:3000
- Jenkins : http://localhost:8080

Récupérer le mot de passe administrateur initial de Jenkins :

```bash
docker exec jenkins-security cat /var/jenkins_home/secrets/initialAdminPassword
```

## Lancer les analyses de sécurité

1. Ouvrir Jenkins sur http://localhost:8080, installer les plugins suggérés (ou ceux déjà
   inclus dans l'image : `workflow-aggregator`, `git`, `docker-workflow`, `htmlpublisher`, `junit`).
2. Créer un job **Pipeline** (ex. `security-audit-juice-shop`).
3. Dans la configuration du job, section **Pipeline** :
   - **Definition** : `Pipeline script from SCM` ;
   - **SCM** : `Git`, **Repository URL** : `/workspace` (chemin interne au conteneur Jenkins,
     monté sur ce dépôt — voir `docker-compose.yml`) ;
   - **Script Path** : `Jenkinsfile`.
4. Lancer un build (**Build Now**).

Le pipeline exécute dans l'ordre :

1. **Checkout** — récupération du code source.
2. **Build / Preparation** — construction de l'image Docker de Juice Shop et démarrage du conteneur cible.
3. **Security Analysis** (**séquentiel** — voir note ci-dessous) :
   - **SAST** avec [Semgrep](https://semgrep.dev/) (règles OWASP Top 10 / JS / TS) ;
   - **SCA** avec [Trivy](https://aquasecurity.github.io/trivy/) (scan du filesystem / dépendances npm) ;
   - **Secret Detection** avec [Gitleaks](https://github.com/gitleaks/gitleaks).
4. **Additional Security Check (DAST)** avec [OWASP ZAP](https://www.zaproxy.org/) (`zap-baseline.py`) contre l'application en cours d'exécution.
5. **Report Generation** — agrégation des résultats (`scripts/aggregate_report.py`) dans `reports/summary.md`.
6. **Notification** — affichage du résumé (simulation d'une notification équipe sécurité / dev ;
   en production ce serait un webhook Slack/Teams ou un email).

Tous les rapports bruts (JSON/HTML) sont archivés dans `reports/` par le job Jenkins
(`archiveArtifacts`).

### Notes / pièges connus

- **Pourquoi le stage 3 est séquentiel et pas parallèle** : sur une machine avec peu de RAM
  disponible, exécuter Semgrep + Trivy (qui télécharge une base de vulnérabilités ~110 Mo au
  premier lancement) + Gitleaks en même temps peut faire planter le moteur Docker Desktop par
  manque de mémoire. Adapter au besoin si votre machine a plus de marge.
- **Checkout Git local** : Jenkins bloque par défaut les checkouts depuis un chemin local (pas
  un vrai remote). C'est déjà autorisé via la variable d'environnement `JAVA_OPTS` du service
  `jenkins` dans `docker-compose.yml` — rien à faire de plus.
- **DAST / OWASP ZAP** : `zap-baseline.py` refuse de s'exécuter si `/zap/wrk` n'est pas un vrai
  point de montage. Le `Jenkinsfile` crée un volume Docker nommé dédié pour cette raison — ne
  pas remplacer ça par un bind-mount du workspace (échoue sous Docker-outside-of-Docker).

### Régénérer le rapport (PDF / Word)

```bash
python3 reports/build_pdf.py    # nécessite: pip install reportlab
python3 reports/build_docx.py   # nécessite: pip install python-docx
```

Les deux scripts lisent `reports/rapport-securite.md` + `reports/analyse-critique.md` (Partie 6,
ajoutée automatiquement en annexe) et régénèrent respectivement `rapport-securite.pdf` et
`rapport-securite.docx`.

## Outils utilisés

| Outil | Type | Rôle |
|---|---|---|
| Semgrep | SAST | Analyse statique du code source (JS/TS), règles OWASP Top 10 |
| Trivy | SCA | Analyse des dépendances npm (CVE connues) |
| Gitleaks | Secret detection | Recherche de secrets/clés codés en dur dans le code |
| OWASP ZAP (baseline) | DAST | Analyse dynamique de l'application en fonctionnement |

## Remédiation

Voir [`remediation/`](remediation/) pour le détail avant/après de chaque correctif appliqué
(SQL Injection, Broken Access Control / IDOR, Hardcoded secret) ainsi que la méthode de
vérification utilisée pour chacun.

## Rapport

Le rapport de sécurité complet (contexte, méthodologie, vulnérabilités, CWE, impacts CIA,
remédiations, pipeline, résultats, décision de déploiement, conclusion) se trouve dans
`reports/rapport-securite.md` (source) / `.pdf` (livrable final).
