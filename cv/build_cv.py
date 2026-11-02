"""Build the academic CV PDF that the page links (Ben-Sapirstein-CV.pdf).

Run from the repo root:  python3 cv/build_cv.py
Needs: reportlab, fonttools, brotli (to read the woff2 fonts in fonts/), pypdf (the leak check reads the PDF).

It also writes the page's Publications and Teaching lists (between the
<!-- cv:... --> markers of index.html), so the page and the PDF show the same facts.

The content is cv/cv.json. cv/export.py writes it from Ben's private CV note, the
one place he edits the CV [Ben 11-02]. This is the public version: it follows the
page's content rule (no theory before publication) and the data-leak rule of the
README (no tool stack, no email, no phone, no private names) [Ben 11-01]; the
leak check stops the build on a hit.

Tune the design values in DESIGN.
"""
from pathlib import Path
import html
import json
import re
import sys
import tempfile

from fontTools.ttLib import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Ben-Sapirstein-CV.pdf"

# Design values: tune here.
DESIGN = {
    "margin_mm": 14,
    "body_pt": 9.0,
    "leading": 1.38,          # line height as a factor of the body size
    "name_pt": 22,
    "section_pt": 8.4,
    "date_col_mm": 26,        # width of the left date column
    "fg": "#1c1b19",
    "muted": "#5d5a54",
    "rule": "#e2dfd8",
    "accent": "#8a4b2a",      # link colour, as on the page
}

# ---------------------------------------------------------------- content
# The content is cv/cv.json, exported from Ben's private CV note by cv/export.py.
# Do not edit cv.json by hand: change the note, then run this script.
NAME = "Ben Sapirstein"
DATA_FILE = ROOT / "cv" / "cv.json"
PAGE = ROOT / "index.html"


def load() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def initials(full: str) -> str:
    """'Guy Mor-Lan' -> 'Mor-Lan, G.'"""
    *given, family = full.split()
    return f"{family}, " + " ".join(f"{g[0]}." for g in given)


def short_url(url: str) -> str:
    return url.split("://", 1)[-1].rstrip("/")

# ---------------------------------------------------------------- fonts
FONTS = {
    "Body": "source-sans-3-latin-400-normal.woff2",
    "Body-Italic": "source-sans-3-latin-400-italic.woff2",
    "Body-Bold": "source-sans-3-latin-600-normal.woff2",
    "Head": "inter-tight-latin-500-normal.woff2",
    "Head-Bold": "inter-tight-latin-600-normal.woff2",
}


def register_fonts(tmp: Path) -> None:
    for name, woff in FONTS.items():
        f = TTFont(ROOT / "fonts" / woff)
        f.flavor = None
        ttf = tmp / f"{name}.ttf"
        f.save(ttf)
        pdfmetrics.registerFont(RLTTFont(name, str(ttf)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic", boldItalic="Body-Bold")


def link(label: str, url: str) -> str:
    return f'<a href="{url}" color="{DESIGN["accent"]}">{label}</a>'


def build(cv: dict) -> None:
    d = DESIGN
    fg, muted, rule = HexColor(d["fg"]), HexColor(d["muted"]), HexColor(d["rule"])
    body_pt = d["body_pt"]
    lead = body_pt * d["leading"]
    st = {
        "name": ParagraphStyle("name", fontName="Head-Bold", fontSize=d["name_pt"],
                               leading=d["name_pt"] * 1.1, textColor=fg),
        "headline": ParagraphStyle("headline", fontName="Head", fontSize=body_pt + 1,
                                   leading=(body_pt + 1) * 1.3, textColor=muted, spaceBefore=3),
        "contact": ParagraphStyle("contact", fontName="Body", fontSize=body_pt,
                                  leading=lead, textColor=fg, spaceBefore=4),
        "section": ParagraphStyle("section", fontName="Head-Bold", fontSize=d["section_pt"],
                                  leading=d["section_pt"] * 1.3, textColor=muted,
                                  spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Body", fontSize=body_pt, leading=lead,
                               textColor=fg, alignment=TA_LEFT),
        "date": ParagraphStyle("date", fontName="Body", fontSize=body_pt, leading=lead,
                               textColor=muted),
        "detail": ParagraphStyle("detail", fontName="Body", fontSize=body_pt, leading=lead,
                                 textColor=muted),
    }
    page_w = A4[0] - 2 * d["margin_mm"] * mm
    date_w = d["date_col_mm"] * mm

    def section(title):
        t = Table([[Paragraph(title.upper(), st["section"])]], colWidths=[page_w])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, rule),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        return t

    def row(date, *paras):
        t = Table([[Paragraph(date, st["date"]), list(paras)]],
                  colWidths=[date_w, page_w - date_w])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return KeepTogether(t)

    contact = "  ·  ".join(link(html.escape(c["label"]), c["url"]) if c["url"] else html.escape(c["label"])
                            for c in cv["contact"])
    story = [Paragraph(NAME, st["name"]), Paragraph(cv["headline"], st["headline"]),
             Paragraph(contact, st["contact"]), Spacer(1, 6), Paragraph(cv["summary"], st["body"])]

    def dated(section_name, rows):
        story.append(section(section_name))
        for r in rows:
            paras = [Paragraph(f"<b>{html.escape(r['title'])}</b>, {html.escape(r['place'])}", st["body"])]
            if r["detail"]:
                paras.append(Paragraph(r["detail"], st["detail"]))
            story.append(row(r["dates"], *paras))

    dated("Education", cv["education"])

    story.append(section("Publications"))
    for p in cv["publications"]:
        authors = ", ".join(f"<b>{initials(a)}</b>" if a == NAME else initials(a) for a in p["authors"])
        ls = " · ".join(link(short_url(l["url"]), l["url"]) for l in p["links"])
        story.append(row(p["year"], Paragraph(f"{authors} <b>{html.escape(p['title'])}.</b> {p['venue']}.", st["body"]),
                         Paragraph(ls, st["body"])))

    dated("Teaching", cv["teaching"])
    dated("Experience", cv["experience"])

    story.append(section("Skills"))
    story.append(row("", Paragraph("<br/>".join(html.escape(s) for s in cv["skills"]), st["body"])))

    story.append(section("Languages"))
    story.append(row("", Paragraph(cv["languages"], st["body"])))

    m = d["margin_mm"] * mm
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=m, rightMargin=m,
                            topMargin=m, bottomMargin=m, title="Ben Sapirstein, CV",
                            author="Ben Sapirstein")
    doc.build(story)
    print(OUT)


# ---------------------------------------------------------------- the page
def write_page(cv: dict) -> None:
    """Write the page's Publications and Teaching lists between their markers."""
    def e(x):
        return html.escape(x, quote=False)
    pubs = []
    for p in cv["publications"]:
        if not p["page"]:
            continue
        authors = ", ".join(f"<strong>{e(a)}</strong>" if a == NAME else e(a) for a in p["authors"])
        ls = " ".join(f'<a href="{html.escape(l["url"])}">{e(l["label"])}</a>' for l in p["links"])
        pubs.append(f"""        <li>
          <span class="title">{e(p["title"])}</span>
          <span class="authors">{authors}</span>
          <span class="venue">{e(p["page_venue"])}</span>
          <span class="pub-links">{ls}</span>
        </li>""")
    teach = [f"        <li>{e(t['title'])}, {e(t['place'])}, {e(t['dates'])}</li>"
             for t in cv["teaching"] if t["page"]]
    page = PAGE.read_text(encoding="utf-8")
    for key, items in (("publications", pubs), ("teaching", teach)):
        pat = re.compile(rf"(<!-- cv:{key} -->\n).*?(\n\s*<!-- /cv:{key} -->)", re.S)
        if not pat.search(page):
            sys.exit(f"build: the markers of {key} are missing in index.html")
        page = pat.sub(lambda m: m.group(1) + "\n".join(items) + m.group(2), page)
    PAGE.write_text(page, encoding="utf-8")
    print(PAGE)


def leak_check() -> None:
    """The data-leak rule of the README: stop on a hit. Needs cv/local.toml."""
    import export
    cfg = export.local()
    if not cfg.get("rules"):
        print("build: no cv/local.toml; the leak check did not run")
        return
    terms = export.rule_terms(Path(cfg["rules"]).expanduser())
    # Every public file: the text files git would publish, and the PDF's text and metadata.
    import subprocess
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--cached", "--others",
                             "--exclude-standard"], capture_output=True, text=True,
                            env={**__import__("os").environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.split()
    texts = {}
    for name in listed:
        path = ROOT / name
        if path.suffix in {".html", ".css", ".md", ".py", ".json", ".svg", ".txt", ""} and path.is_file():
            texts[name] = path.read_text(encoding="utf-8", errors="ignore")
    if OUT.exists():
        from pypdf import PdfReader
        pdf = PdfReader(str(OUT))
        texts[OUT.name] = " ".join(pg.extract_text() for pg in pdf.pages) + " " + " ".join(
            str(v) for k, v in (pdf.metadata or {}).items() if "Date" not in k)
    hits = export.check_leaks(texts, terms, cfg.get("markers", []))
    if hits:
        sys.exit("build: data leak, fix the source note:\n  " + "\n  ".join(hits))
    print(f"leak check: clean ({len(terms)} names, emails, phone numbers, private paths)")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "cv"))
    import export
    export.main()
    cv = load()
    write_page(cv)
    with tempfile.TemporaryDirectory() as tmp:
        register_fonts(Path(tmp))
        build(cv)
    leak_check()
