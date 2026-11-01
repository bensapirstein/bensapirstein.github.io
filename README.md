# bensapirstein.github.io

Ben Sapirstein's personal academic page. One static page: `index.html`, `style.css`, `fonts/`, `assets/`. No build step, no scripts, no external requests at runtime.

## Rules

Read these before you edit anything here. This repository is public once it is published, so every file in it is public: the page, the CV, this README, the scripts and their comments.

1. Data leak, strictly [Ben 11-01]. No file here names the studio's design tool stack (its font editors, its rendering and animation tools, its font source formats), its internal project or font names, its private notes or their paths, or any unpublished research. No file carries an email address, a phone number or a street address. A public URL that Ben's own profiles already show (GitHub, X, LinkedIn, alefalif.com, the publication pages) is fine. Before a commit, search the page, the CV text and this README for these; what you find comes out, and the report lists it. The git history is public too: the history was squashed to one clean commit on 1 November 2026, before the first publish, and commits carry the GitHub noreply address, never a personal email.
2. Content rule [Ben 10-26]. The page stays with the publications: no theory before it is published. Alef Alif Studio stays as one reference under Projects.
3. Facts come from Ben's private notes (the CV master and its academic selection), never from memory. Change a fact there first, then here.
4. The publish (the GitHub repository, the push, Pages) is Ben's own step. Agents prepare it; Ben says "publish the site".

## Preview

A local static server serves it over HTTP at http://localhost:7070/web/bensapirstein.github.io/, with a card under Websites on http://localhost:7070/. Serve it over HTTP; the font preload does not work from a `file://` URL.

## Edit

- Text: edit `index.html`. Each section is marked with an `id` (`about`, `research`, `publications`, `projects`, `teaching`).
- A new publication: copy one `<li>` in `ol.pubs` and fill the four spans (title, authors, venue, links). The list is newest first.
- Design values: the variables in `:root` at the top of `style.css` (column width, colours, fonts). Dark mode follows the system setting.
- Facts: see rule 3.

## Portrait

Source: `~/Pictures/Academic Ben/042A7838.JPG` (8192 × 5464, untouched). The page uses a 4:5 crop at two sizes, in WebP and JPEG:

| File | Size | Use |
|---|---|---|
| `assets/portrait-1x.*` | 400 × 500 | default and small screens |
| `assets/portrait.*` | 800 × 1000 | high-density screens, Open Graph |

To recrop, run on the source with Pillow: crop `(2679, 0, 7050, 5464)`, resize to 400 × 500 and 800 × 1000, save JPEG quality 82 and WebP quality 80.

## Fonts

Self-hosted subsets, SIL OFL 1.1 (licences in `fonts/`): Inter Tight 500 and 600 (name, headings, link labels), Source Sans 3 400, 400 italic and 600 (body). Only the Latin subsets load.

## CV

The header links `Ben-Sapirstein-CV.pdf`, a one-page academic CV built by `cv/build_cv.py` in the page's fonts.

- Build: `python3 cv/build_cv.py` from the repo root. It needs `reportlab`, `fonttools` and `brotli`.
- Content: the lists at the top of the script. Facts: see rule 3. The CV follows rule 1: no tool stack, no email, no phone.
- Design values: `DESIGN` in the script (margins, sizes, colours).
- The PDF is committed with the page. Rebuild it and commit it with every change to the script.

## Publish

GitHub Pages serves the repository root on `main`, like `shams-nlp.github.io`. This is Ben's step (rule 4).

1. Create the repository `bensapirstein/bensapirstein.github.io` on GitHub (public).
2. `git remote add origin git@github.com:bensapirstein/bensapirstein.github.io.git`
3. `git push -u origin main`
4. GitHub → Settings → Pages: Source "Deploy from a branch", branch `main`, folder `/ (root)`.
5. The page appears at https://bensapirstein.github.io/ within a few minutes.

Optional: a custom domain needs a `CNAME` file in the root and a DNS record.

## Open items

The project's hub note in Ben's private notes, "Personal site", holds the open items and the decisions.
