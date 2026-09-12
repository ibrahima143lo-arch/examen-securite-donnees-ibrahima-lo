# Partie 6 — Analyse critique

**Question : Un outil de sécurité qui ne détecte aucune vulnérabilité peut-il garantir
qu'une application est sécurisée ?**

Non. L'absence de finding remonté par un outil signifie seulement que **cet outil, avec sa
configuration actuelle, n'a rien trouvé** — ce n'est en aucun cas une preuve d'absence de
vulnérabilité. Cette limite se comprend à travers plusieurs angles complémentaires.

**Faux négatifs.** Chaque outil ne détecte que ce que ses règles ou son moteur savent
reconnaître. Semgrep ne signale que les patterns couverts par son jeu de règles ; il n'aurait
par exemple jamais détecté seul la faille IDOR sur `/rest/basket/:id` de ce rapport (V3), car
il s'agit d'un défaut de *logique métier* — le code est syntaxiquement correct, il manque
simplement une vérification d'autorisation que l'outil ne peut pas deviner sans connaître les
règles métier de l'application. De même, Trivy et Gitleaks ne trouvent que des CVE publiées ou
des motifs de secrets connus : un secret encodé différemment, ou une dépendance vulnérable non
encore répertoriée dans une base CVE, passera inaperçu. OWASP ZAP en mode « baseline » est
volontairement non intrusif et ne couvre que ce que son crawler automatique atteint, sans
authentification avancée ni scénarios métier complexes.

**Faux positifs.** À l'inverse, un outil « silencieux » peut aussi l'être parce qu'il a été
mal configuré (règles désactivées, chemin exclu, seuil de sévérité trop élevé) plutôt que
parce que l'application est saine — et un outil trop permissif en configuration par défaut
peut masquer de vrais problèmes tout en générant, sur d'autres projets, des alertes non
pertinentes qui, à force, entraînent une désensibilisation de l'équipe (« alert fatigue »),
un risque tout aussi dangereux qu'un faux négatif.

**Couverture des règles.** Un SAST/DAST/SCA couvre un ensemble de catégories connues (souvent
alignées sur l'OWASP Top 10 ou des bases CWE), mais la surface de risque réelle d'une
application (architecture, flux de données propriétaires, règles métier de contrôle d'accès,
interactions entre composants) dépasse toujours ce périmètre. Dans ce projet, sur les six
vulnérabilités identifiées, seule une partie (SQLi, secrets, dépendances) est directement du
ressort d'un outil automatisé ; l'IDOR et certains choix d'architecture nécessitent une revue
humaine ciblée.

**Importance de l'analyse humaine.** Un pipeline automatisé est un filet de sécurité
nécessaire — il garantit la reproductibilité et empêche la régression des problèmes déjà
connus — mais il doit être complété par une revue de code manuelle, une analyse de risques
contextuelle et, idéalement, un test d'intrusion ciblé sur la logique métier. La bonne
pratique n'est donc jamais « le scanner est vert, on déploie », mais « le scanner ne remonte
rien connu, **et** un humain a validé les zones à risque spécifiques à l'application » avant
toute décision de mise en production.

*(≈ 420 mots)*
