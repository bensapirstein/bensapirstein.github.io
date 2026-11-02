"""Export the public CV data (cv/cv.json) from Ben's private CV note.

Run through build_cv.py, or alone:  python3 cv/export.py
The paths of the private note and of the rule list are in cv/local.toml, which
git ignores (keys: `master`, `rules`, and `markers`: private words such as
path parts that must never appear in a public file). Without that file, the export is skipped
and the committed cv/cv.json is used as it is.

Only entries tagged #cv/site leave the note; #cv/page also lists an entry on the
web page. Text between %% marks stays private. The data-leak check runs on the
result (check_leaks below); a hit stops the build.
"""
from pathlib import Path
import json
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "cv" / "local.toml"
OUT = ROOT / "cv" / "cv.json"

TAG = re.compile(r"#cv/[\w-]+")
PRIVATE = re.compile(r"%%.*?%%", re.S)
MDLINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
PROVENANCE = re.compile(r"\s*\[(Ben|files)[^\]]*\]")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\+?\(?\d[\d\s()-]{7,}\d")


def clean(text: str) -> str:
    """Drop private comments, tags and provenance marks; keep the words."""
    text = PRIVATE.sub("", text)
    text = TAG.sub("", text)
    text = PROVENANCE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def links(text: str) -> list:
    return [{"label": l, "url": u} for l, u in MDLINK.findall(text)]


def plain(text: str) -> str:
    """Markdown links to their label; *italics* to <i>."""
    text = MDLINK.sub(lambda m: m.group(1), text)
    return re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)


def years(span: str) -> str:
    """'2024-11 to 2026-06' -> '2024 – 2026'; an unknown end ('[...]') stays open."""
    span = span.strip()
    if " to " not in span:
        return span
    a, b = (s.strip() for s in span.split(" to ", 1))
    a = a.split("-")[0]
    b = "" if b.startswith("[") else ("present" if b == "present" else b.split("-")[0])
    return f"{a} – {b}".rstrip()


def sections(md: str) -> dict:
    out, name = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            out[name] = []
        elif name:
            out[name].append(line)
    return out


def entries(lines: list) -> list:
    """Bold-headed entries: the head line, then its body lines up to a blank line."""
    items, cur = [], None
    for line in lines:
        if line.startswith("**"):
            cur = {"head": line, "body": []}
            items.append(cur)
        elif not line.strip():
            cur = None
        elif cur is not None:
            cur["body"].append(line)
    return items


def tags(line: str) -> set:
    return set(TAG.findall(PRIVATE.sub("", line)))


def head_parts(head: str):
    m = re.match(r"\*\*(.+?)\*\*(.*)", head)
    bold, rest = m.group(1), clean(m.group(2))
    rest = [p.strip() for p in rest.split("·") if p.strip()]
    return bold, rest


def export(master: Path) -> dict:
    md = master.read_text(encoding="utf-8")
    sec = sections(md)
    data = {"headline": "", "contact": [], "summary": "", "education": [],
            "publications": [], "teaching": [], "experience": [],
            "skills": [], "languages": ""}

    for line in sec.get("Identity", []):
        if "#cv/site" not in tags(line):
            continue
        if line.startswith("- Academic:"):
            data["headline"] = clean(line.split(":", 1)[1])
        elif line.startswith("Site contact:"):
            for part in clean(line.split(":", 1)[1]).split("·"):
                part = part.strip()
                ls = links(part)
                data["contact"].append(ls[0] if ls else {"label": part, "url": None})
        elif line.startswith("Site summary:"):
            data["summary"] = plain(clean(line.split(":", 1)[1]))

    for e in entries(sec.get("Experience", [])):
        if "#cv/site" in tags(e["head"]):
            bold, rest = head_parts(e["head"])
            place, title = (s.strip() for s in bold.split(" — ", 1))
            data["experience"].append({"dates": years(rest[0]), "title": title, "place": place,
                                       "detail": plain(clean(" ".join(e["body"])))})

    for e in entries(sec.get("Education", [])):
        if "#cv/site" in tags(e["head"]):
            bold, rest = head_parts(e["head"])
            place, title = (s.strip() for s in bold.split(" — ", 1))
            detail = " ".join([f"{r}." for r in rest[1:]] + [clean(" ".join(e["body"]))])
            data["education"].append({"dates": years(rest[0]), "title": title, "place": place,
                                      "detail": plain(detail).strip()})

    for e in entries(sec.get("Teaching", [])):
        if "#cv/site" in tags(e["head"]):
            bold, rest = head_parts(e["head"])
            left, role = (s.strip() for s in bold.split(" — ", 1))
            course, place = (left.rsplit(", ", 1) if ", " in left else (None, left))
            data["teaching"].append({"dates": years(rest[0]),
                                     "title": f"{role}, {course}" if course else role,
                                     "place": place, "detail": plain(clean(" ".join(e["body"]))),
                                     "page": "#cv/page" in tags(e["head"])})

    for e in entries(sec.get("Publications", [])):
        if "#cv/site" not in tags(e["head"]):
            continue
        bold, rest = head_parts(e["head"])
        f = {}
        for line in e["body"]:
            if ":" in line:
                k, v = line.split(":", 1)
                f[k.strip().lower()] = v
        data["publications"].append({
            "year": rest[0], "title": bold,
            "authors": [a.strip() for a in clean(f.get("authors", "")).split(",")],
            "venue": plain(clean(f.get("venue", ""))),
            "page_venue": clean(f.get("page venue", "")),
            "links": links(PRIVATE.sub("", f.get("links", ""))),
            "page": "#cv/page" in tags(e["head"])})

    data["skills"] = [clean(l) for l in sec.get("Skills", []) if "#cv/site" in tags(l)]
    langs = [clean(l) for l in sec.get("Languages", []) if "#cv/site" in tags(l)]
    data["languages"] = " · ".join(langs)
    return data


def rule_terms(rules: Path) -> list:
    """The forbidden names: every name in the parentheses of the rule line."""
    for line in rules.read_text(encoding="utf-8").splitlines():
        if "None names the" in line:
            terms = []
            for group in re.findall(r"\(([^)]*)\)", line):
                for t in re.split(r"[,:]", group):
                    t = t.strip()
                    if t and " " not in t:
                        terms.append(t)
            if terms:
                return terms
    sys.exit("export: no rule line found; the leak check cannot run, so the build stops")


def check_leaks(texts: dict, terms: list, markers: list = ()) -> list:
    """Return 'file: hit' for each forbidden name, email or phone number found."""
    hits = []
    for name, text in texts.items():
        # Read the words and the link targets, not the drawing data: SVG path
        # data looks like phone numbers.
        if not name.endswith(".py") and re.search(r"mailto:|tel:", text):
            hits.append(f"{name}: a mailto or tel link")
        text = re.sub(r"<svg.*?</svg>", " ", text, flags=re.S)
        targets = " ".join(re.findall(r'(?:href|src|content)="([^"]*)"', text))
        text = re.sub(r"<[^>]+>", " ", text) + " " + targets.replace("mailto:", " ").replace("tel:", " ")
        for t in terms:
            # A long name matches inside a compound word too; a short one
            # (four letters or fewer) only as a word, so ordinary words pass.
            pat = re.escape(t) if len(t) >= 5 else rf"(?<![A-Za-z]){re.escape(t)}(?![a-z])"
            if re.search(pat, text, re.I):
                hits.append(f"{name}: {t}")
        for m in EMAIL.findall(text):
            if not m.startswith("git@"):  # an SSH remote, not a mailbox
                hits.append(f"{name}: an email")
        for m in PHONE.findall(text):
            digits = re.sub(r"\D", "", m)
            if len(digits) >= 9:
                hits.append(f"{name}: a phone number")
        for marker in (("%%",) if not name.endswith(".py") else ()) + tuple(markers):
            if marker in text:
                hits.append(f"{name}: {marker}")
    return hits


def local() -> dict:
    return tomllib.loads(LOCAL.read_text()) if LOCAL.exists() else {}


def main() -> None:
    cfg = local()
    if not cfg.get("master"):
        print("export: no cv/local.toml; using the committed cv/cv.json")
        return
    data = export(Path(cfg["master"]).expanduser())
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
