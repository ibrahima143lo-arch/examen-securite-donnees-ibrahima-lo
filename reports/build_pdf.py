#!/usr/bin/env python3
"""Renders rapport-securite.md (+ analyse-critique.md as an annex) into a
formatted PDF using reportlab. A small, purpose-built markdown->reportlab
converter — not a general markdown engine — tailored to this report's needs
(headings, tables, bold/code inline spans, bullet/numbered lists, fences)."""
import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    ListFlowable, ListItem, Preformatted, KeepTogether
)
from reportlab.lib.enums import TA_CENTER

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_MD = os.path.join(HERE, "rapport-securite.md")
ANNEX_MD = os.path.join(HERE, "analyse-critique.md")
OUT_PDF = os.path.join(HERE, "rapport-securite.pdf")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleFR", parent=styles["Title"], fontSize=20, spaceAfter=6))
styles.add(ParagraphStyle(name="SubTitle", parent=styles["Normal"], fontSize=10.5, textColor=colors.HexColor("#444444"), spaceAfter=2))
styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=15, spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#1a1a2e")))
styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=8, alignment=0))
styles.add(ParagraphStyle(name="Cell", parent=styles["Normal"], fontSize=8, leading=10.5))
styles.add(ParagraphStyle(name="CellHead", parent=styles["Normal"], fontSize=8.3, leading=10.5, textColor=colors.white, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="BulletFR", parent=styles["Body"], leftIndent=0, spaceAfter=3))
styles.add(ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER))


EMOJI_MAP = {
    "↓": "|",       # ↓  (used in the pipeline flow diagram)
    "\U0001F534": "[ROUGE] ",   # 🔴
    "\U0001F7E0": "[ORANGE] ",  # 🟠
    "\U0001F7E2": "[VERT] ",    # 🟢
    "≈": "~",       # ≈
    "✅": "[OK] ",   # ✅
    "⚠": "[!] ",    # ⚠
    "️": "",        # variation selector that tags emoji
}


def ascii_safe(text: str) -> str:
    """Core PDF fonts (Helvetica/Courier, WinAnsiEncoding) can't render emoji
    or some symbol characters — swap them for plain-text equivalents so they
    don't silently disappear or render as tofu boxes."""
    for k, v in EMOJI_MAP.items():
        text = text.replace(k, v)
    return text


def inline(text: str) -> str:
    """Escape XML then translate a small subset of markdown inline syntax
    into reportlab's mini-markup (bold, inline code, links stripped to text)."""
    text = ascii_safe(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    return text


def parse_table(lines, i):
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(row)
        i += 1
    if len(rows) >= 2:
        del rows[1]  # separator row (---|---)
    return rows, i


def make_table(rows, col_widths=None):
    ncols = len(rows[0])
    data = []
    for r, row in enumerate(rows):
        style = styles["CellHead"] if r == 0 else styles["Cell"]
        data.append([Paragraph(inline(c), style) for c in row])
    if col_widths is None:
        avail = 17.2 * cm
        col_widths = [avail / ncols] * ncols
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a67")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_story(lines, story, skip_h1=False):
    i = 0
    in_code = False
    code_buf = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_text = ascii_safe("\n".join(code_buf))
                story.append(Preformatted(code_text, styles["Code"] if "Code" in styles else ParagraphStyle(name="CodeTmp", fontName="Courier", fontSize=7.5, leading=9)))
                story.append(Spacer(1, 6))
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            i += 1
            continue

        if stripped.startswith("# "):
            if not skip_h1:
                story.append(Paragraph(inline(stripped[2:]), styles["TitleFR"]))
            i += 1
            continue

        if stripped.startswith("## "):
            story.append(Paragraph(inline(stripped[3:]), styles["H1"]))
            i += 1
            continue

        if stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
            story.append(Paragraph(inline(stripped), styles["Body"]))
            i += 1
            continue

        if stripped.startswith("|"):
            rows, i = parse_table(lines, i)
            story.append(make_table(rows))
            story.append(Spacer(1, 10))
            continue

        if re.match(r"^\d+\.\s", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                txt = re.sub(r"^\d+\.\s", "", lines[i].strip())
                items.append(ListItem(Paragraph(inline(txt), styles["Body"]), leftIndent=12))
                i += 1
            story.append(ListFlowable(items, bulletType="1", start=1))
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                txt = lines[i].strip()[2:]
                items.append(ListItem(Paragraph(inline(txt), styles["Body"]), leftIndent=12))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", start="circle"))
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("_") and stripped.endswith("_"):
            story.append(Paragraph(f"<i>{inline(stripped[1:-1])}</i>", styles["Body"]))
            i += 1
            continue

        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            story.append(Paragraph(f"<i>{inline(stripped[1:-1])}</i>", styles["Body"]))
            i += 1
            continue

        story.append(Paragraph(inline(stripped), styles["Body"]))
        i += 1


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"Page {doc.page}")
    canvas.drawString(2 * cm, 1.2 * cm, "Examen final — Sécurité des données — Ibrahima Lo")
    canvas.restoreState()


def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def build_toc(main_lines):
    """Table des matières générée à partir des titres de section réels (## N. ...)."""
    entries = [ln.strip()[3:] for ln in main_lines if ln.strip().startswith("## ")]
    entries.append("Annexe — Partie 6 : Analyse critique")
    flow = [Paragraph("Sommaire", styles["H1"])]
    for e in entries:
        flow.append(Paragraph(inline(e), styles["Body"]))
    flow.append(PageBreak())
    return flow


def main():
    doc = SimpleDocTemplate(
        OUT_PDF, pagesize=A4,
        leftMargin=1.7 * cm, rightMargin=1.7 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title="Rapport de sécurité — OWASP Juice Shop",
        author="Ibrahima Lo",
    )
    main_lines = read_lines(MAIN_MD)
    annex_lines = read_lines(ANNEX_MD)

    # Split the header block (title + author/role/... lines) from "## 1. Introduction"
    # onward, so a real table of contents can be inserted right after the header.
    split_at = next(idx for idx, ln in enumerate(main_lines) if ln.strip().startswith("## 1."))
    header_lines, body_lines = main_lines[:split_at], main_lines[split_at:]

    story = []
    build_story(header_lines, story)
    story.append(PageBreak())
    story.extend(build_toc(main_lines))
    build_story(body_lines, story)

    story.append(PageBreak())
    story.append(Paragraph("Annexe — Partie 6 : Analyse critique", styles["TitleFR"]))
    story.append(Spacer(1, 6))
    build_story(annex_lines, story, skip_h1=True)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Written: {OUT_PDF}")


if __name__ == "__main__":
    main()
