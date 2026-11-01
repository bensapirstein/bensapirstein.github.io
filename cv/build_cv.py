"""Build the academic CV PDF that the page links (Ben-Sapirstein-CV.pdf).

Run from the repo root:  python3 cv/build_cv.py
Needs: reportlab, fonttools, brotli (to read the woff2 fonts in fonts/).

Facts come from Ben's private notes (the CV master and its academic selection).
Change a fact there first, then here. This is the public version: it follows the
page's content rule (no theory before publication) and the data-leak rule of the
README (no tool stack, no email, no phone, no private names) [Ben 11-01]. The
contact line names Alef Alif, the studio site, in place of Google Scholar [Ben 11-01].

Tune the design values in DESIGN.
"""
from pathlib import Path
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
NAME = "Ben Sapirstein"
HEADLINE = "Computational linguistics · typography · human-computer interaction"
CONTACT = [
    ("Tel Aviv-Yafo, Israel", None),
    ("bensapirstein.github.io", "https://bensapirstein.github.io/"),
    ("alefalif.com", "https://alefalif.com"),
    ("github.com/bensapirstein", "https://github.com/bensapirstein"),
]
# Ben's wording (LinkedIn About, kept in Bios.md).
SUMMARY = ("I explore the meeting point of computer science, linguistics, and typography. "
           "I am interested in how the visual dimension of writing can shape understanding, "
           "and I develop approaches that treat the form of text itself as a source of information. "
           "In computational historical linguistics, I study how languages evolve and relate "
           "to one another, with a focus on the Semitic family.")

# (dates, title, place, detail)
EDUCATION = [
    ("2022 – 2026", "M.Sc. Machine Learning & Data Science", "Reichman University, Herzliya",
     "GPA 97/100. Thesis: SHAMS, an audio-grounded pronunciation benchmark for Levantine Arabic."),
    ("2017 – 2020", "B.Sc. Computer Science", "Hebrew University of Jerusalem",
     "GPA 91/100. Algorithms, data science, deep learning, image processing, NLP, AI."),
]

# (year, authors, title, venue, [(label, url)])
PUBLICATIONS = [
    ("2026", "<b>Sapirstein, B.</b>, Mattar, R., Mor-Lan, G., Mohamed, A., Cerqueglini, L., Alper, M.",
     "SHAMS: An Audio-Grounded Pronunciation Benchmark for Levantine Arabic.",
     "<i>Proceedings of the Fourth Arabic Natural Language Processing Conference (ArabicNLP @ EMNLP 2026)</i>.",
     [("arXiv:2610.01427", "https://arxiv.org/abs/2610.01427"),
      ("shams-nlp.github.io", "https://shams-nlp.github.io/")]),
    ("2025", "<b>Sapirstein, B.</b>",
     "Standardizing Phonetic Transcriptions for Kitchen et al.'s Comparative Wordlist on Semitic "
     "Languages with Language-Specific Orthography Profiles.",
     "<i>Computer-Assisted Language Comparison in Practice</i>, 8(2), 95–105.",
     [("doi:10.15475/calcip.2025.2.5", "https://doi.org/10.15475/calcip.2025.2.5")]),
    ("2025", "<b>Sapirstein, B.</b>",
     "Pixels at BAREC Shared Task 2025: Visual Arabic Readability Assessment.",
     "<i>Proceedings of the Third Arabic Natural Language Processing Conference: Shared Tasks</i>, 350–356.",
     [("ACL Anthology", "https://aclanthology.org/2025.arabicnlp-sharedtasks.48/")]),
]

# Public version: only the projects the page lists; no unpublished research line [Ben 10-30].
RESEARCH = [
    ("SHAMS", "Levantine Arabic pronunciation benchmark: dataset, evaluation code, and project page."),
]

TEACHING = [
    ("Fall 2025", "Teaching Assistant, Computational Thinking and Programming in Python",
     "Reichman University", "Weekly tutoring for undergraduates."),
    ("Fall 2025", "Course Assistant, Information Theory", "Reichman University", ""),
    ("2020 – 2021", "Python Instructor", "Tech2Peace",
     "Python tutor in a joint Israeli-Palestinian high-tech and peacebuilding seminar. "
     "Organized a hackathon with Madrasa in which teams built tools for teaching Palestinian "
     "dialectal Arabic to Hebrew speakers."),
]

EXPERIENCE = [
    ("2024 – 2026", "Data Scientist", "Microsoft, Herzliya",
     "Fine-tuned large language models to autonomously generate security event detectors. "
     "Designed and implemented system workflows, analyzed sample data and reasoning outputs. Azure OpenAI."),
    ("2023 – 2024", "Algorithm Developer, Deep Learning", "Mobileye, Ramat Gan",
     "Developed and trained real-time segmentation networks for autonomous vehicles, covering the "
     "pipeline from data engineering through model architecture to deployment. TensorFlow, Python, AWS, GCP."),
]

SKILLS = [
    "Deep learning, computer vision, NLP · Python, C++, TensorFlow, AWS, GCP, Azure OpenAI",
    "Linguistic data modeling, CLDF, comparative method, phonetic transcription",
]
LANGUAGES = "Hebrew (native) · English (fluent) · French (advanced) · Arabic (intermediate)"

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


def build() -> None:
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

    story = [Paragraph(NAME, st["name"]), Paragraph(HEADLINE, st["headline"]),
             Paragraph("  ·  ".join(link(l, u) if u else l for l, u in CONTACT), st["contact"]),
             Spacer(1, 6), Paragraph(SUMMARY, st["body"])]

    story.append(section("Education"))
    for date, title, place, detail in EDUCATION:
        story.append(row(date, Paragraph(f"<b>{title}</b>, {place}", st["body"]),
                         Paragraph(detail, st["detail"])))

    story.append(section("Publications"))
    for year, authors, title, venue, links in PUBLICATIONS:
        ls = " · ".join(link(l, u) for l, u in links)
        story.append(row(year, Paragraph(f"{authors} <b>{title}</b> {venue}", st["body"]),
                         Paragraph(ls, st["body"])))

    story.append(section("Research"))
    for name, line in RESEARCH:
        story.append(row("", Paragraph(f"<b>{name}</b>. {line}", st["body"])))

    story.append(section("Teaching"))
    for date, title, place, detail in TEACHING:
        paras = [Paragraph(f"<b>{title}</b>, {place}", st["body"])]
        if detail:
            paras.append(Paragraph(detail, st["detail"]))
        story.append(row(date, *paras))

    story.append(section("Experience"))
    for date, title, place, detail in EXPERIENCE:
        story.append(row(date, Paragraph(f"<b>{title}</b>, {place}", st["body"]),
                         Paragraph(detail, st["detail"])))

    story.append(section("Skills"))
    story.append(row("", Paragraph("<br/>".join(SKILLS), st["body"])))

    story.append(section("Languages"))
    story.append(row("", Paragraph(LANGUAGES, st["body"])))

    m = d["margin_mm"] * mm
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=m, rightMargin=m,
                            topMargin=m, bottomMargin=m, title="Ben Sapirstein, CV",
                            author="Ben Sapirstein")
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        register_fonts(Path(tmp))
        build()
