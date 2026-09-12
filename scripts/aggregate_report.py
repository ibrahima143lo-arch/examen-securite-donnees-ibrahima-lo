#!/usr/bin/env python3
"""Aggregates SAST/SCA/Secret-detection/DAST tool outputs into one summary.md
used by the 'Report Generation' and 'Notification' stages of the Jenkinsfile."""
import json
import os
from datetime import datetime, timezone

REPORTS_DIR = os.environ.get("REPORTS_DIR", "/workspace/reports")


def load_json(name):
    path = os.path.join(REPORTS_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def count_semgrep(data):
    if not data:
        return 0, 0, 0
    results = data.get("results", [])
    crit = sum(1 for r in results if r.get("extra", {}).get("severity") == "ERROR")
    med = sum(1 for r in results if r.get("extra", {}).get("severity") == "WARNING")
    low = len(results) - crit - med
    return crit, med, low


def count_trivy(data):
    if not data:
        return {}
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for result in data.get("Results", []) or []:
        for vuln in result.get("Vulnerabilities", []) or []:
            sev = vuln.get("Severity", "UNKNOWN")
            counts[sev] = counts.get(sev, 0) + 1
    return counts


def count_gitleaks(data):
    if data is None:
        return 0
    if isinstance(data, list):
        return len(data)
    return 0


def count_zap(data):
    if not data:
        return {}
    counts = {}
    for site in data.get("site", []) or []:
        for alert in site.get("alerts", []) or []:
            risk = alert.get("riskdesc", "Unknown").split(" ")[0]
            counts[risk] = counts.get(risk, 0) + 1
    return counts


def main():
    semgrep = load_json("semgrep-report.json")
    trivy = load_json("trivy-report.json")
    gitleaks = load_json("gitleaks-report.json")
    zap = load_json("zap-report.json")

    s_crit, s_med, s_low = count_semgrep(semgrep)
    t_counts = count_trivy(trivy)
    g_count = count_gitleaks(gitleaks)
    z_counts = count_zap(zap)

    lines = []
    lines.append("# Résumé du pipeline de sécurité")
    lines.append("")
    lines.append(f"Généré le : {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Résultats par outil")
    lines.append("")
    lines.append("| Outil | Type | Findings clés |")
    lines.append("|---|---|---|")
    lines.append(f"| Semgrep | SAST | {s_crit} error / {s_med} warning / {s_low} info |")
    lines.append(
        "| Trivy | SCA | "
        f"{t_counts.get('CRITICAL', 0)} critical / {t_counts.get('HIGH', 0)} high / "
        f"{t_counts.get('MEDIUM', 0)} medium / {t_counts.get('LOW', 0)} low |"
    )
    lines.append(f"| Gitleaks | Secret detection | {g_count} secret(s) détecté(s) |")
    zap_summary = ", ".join(f"{k}: {v}" for k, v in z_counts.items()) or "aucune donnée"
    lines.append(f"| OWASP ZAP | DAST | {zap_summary} |")
    lines.append("")

    critical_total = s_crit + t_counts.get("CRITICAL", 0) + g_count + z_counts.get("High", 0)
    lines.append("## Décision automatique (seuil qualité)")
    lines.append("")
    if critical_total > 0:
        lines.append(
            f"⚠️ {critical_total} finding(s) de sévérité critique/haute détecté(s) — "
            "voir PARTIE 5 du rapport pour la décision de déploiement argumentée."
        )
    else:
        lines.append("✅ Aucun finding critique/haut détecté par les outils automatisés sur ce run.")
    lines.append("")
    lines.append(
        "_Ce résumé automatique ne remplace pas l'analyse humaine : voir la Partie 6 "
        "du rapport (analyse critique) pour les limites des outils (faux positifs / faux négatifs)._"
    )

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(os.path.join(REPORTS_DIR, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
