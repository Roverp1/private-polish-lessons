# Local source library

`catalog.json` is the generated, tracked inventory. Originals and extracted text stay
in the ignored `/reference-materials/` directory, with source filenames preserved.
Run commands from the repository root; the script also resolves paths correctly
when invoked by absolute path from another directory. Python 3 and its standard
library are sufficient apart from the command-line tools below.

## Start here

```sh
python3 scripts/library.py inspect
python3 scripts/library.py inspect umcs-verbs
python3 scripts/library.py search 'czas teraźniejszy' --source umcs-verbs --limit 5
python3 scripts/library.py pages umcs-verbs --pdf 5 --max-chars 3500
python3 scripts/library.py pages hurra-1-student --pdf 10 --max-chars 2500
python3 scripts/library.py pages odkrywamy --pdf 33-35 --ocr --max-chars 3000
python3 scripts/library.py inspect odkrywamy --pdf 33-35
```

Use `inspect` for IDs, then search for a topic and retrieve a small page range.
`pages --pdf` accepts **1-based PDF pages**, at most five at a time. It defaults to
4,000 characters per page, allows 1–6,000 via `--max-chars`, and caps total output
at 20,000 characters. Explicit truncation notices identify clipped output.
`pages` returns the text layer unless `--ocr` is supplied; OCR is never automatic.
Do not pass whole PDFs to a file reader or render a whole book.

Search is case-insensitive **literal** matching, one result per matching line,
with PDF page numbers and snippets of at most 241 characters. It searches cached
pages, never the original PDF. It prefers usable cached OCR where available,
skips low-quality pages, and reports how many it skipped. A failed search is not
evidence that a topic is absent from a scanned book.

```sh
python3 scripts/library.py search 'czas' --source umcs-verbs --limit 5 --offset 5
python3 scripts/library.py search 'koniugacja' --source odkrywamy --pdf 33-35 --limit 5
```

`--limit` is 1–50 (default 10); `--offset` paginates matching lines. Repeat
`--source ID` to select several books, or omit it to search all indexed PDFs.
`search --pdf` requires exactly one source and is bounded to five pages.

## Stable IDs and current coverage

The initial inventory contains **13 PDFs / 2,211 PDF pages / 400 MP3 files**.
Audio totals about **5 hours 32 minutes**. Each MP3 has its original relative
path, filename, SHA-256, duration in seconds, level, and associated book ID in
the catalogue's `audio` array. This is an inventory, not a review of every
recording. Individually checked exercise/track matches are in `teaching-map.md`.

| ID | Source | Level | PDF pages |
| --- | --- | --- | ---: |
| `hurra-1-student` | HURRA 1 student book, Nowa Edycja | A1 | 196 |
| `hurra-1-workbook` | HURRA 1 workbook, Nowa Edycja | A1 | 144 |
| `hurra-1-guide` | HURRA 1 teacher guide, Nowa Edycja | A1 | 152 |
| `hurra-2-student` | HURRA 2 student book, Nowa Edycja | A2 | 196 |
| `hurra-2-workbook` | HURRA 2 workbook, Nowa Edycja | A2 | 108 |
| `hurra-3-student` | HURRA 3 student book, Nowa Edycja | B1 | 212 |
| `hurra-3-workbook` | HURRA 3 workbook, Nowa Edycja | B1 | 132 |
| `hurra-3-guide` | HURRA 3 teacher guide, Nowa Edycja | B1 | 164 |
| `krok-a1` | Polski krok po kroku A1 | A1 | 172 |
| `krok-a2` | Polski krok po kroku A2 | A2 | 155 |
| `odkrywamy` | Odkrywamy język polski | Unverified | 202 |
| `umcs-cases` | Gramatyka z kulturą. Przez przypadki | Unverified | 131 |
| `umcs-verbs` | Gramatyka z kulturą. Przez osoby | Unverified | 247 |

Series levels are filename/series metadata, not page-level teaching judgments.
The UMCS cases book is `142944-gramatyka-z-kultura.pdf`; the verbs book is
`Gramatyka-z-kultura.-Przez-osoby.-Logo.pdf`.

All PDF pages have individual text extraction caches. Useful initial pointers:

- UMCS cases: contents at PDF **4**; UMCS verbs: contents at PDF **5**.
- Usable text-layer opening pages are recorded in `frontmatter`.
- Odkrywamy: all 202 text-layer pages are empty. OCR is cached only for PDF
  **1–5** (contents at 3–5) and **33–35** (present tense / conjugation / modal verbs).
- Both HURRA 2 books: their entire text layers contain only a Telegram watermark.
  OCR is cached for PDF **1–5** of each. The student book's dense contents pages
  **4–5** are flagged `suspect-garbled`; the workbook contents are at PDF **5**.

These are extraction pointers, not a complete-book review or verified lesson map.
Future teaching maps should cite these IDs plus explicit PDF page numbers.

## Build or refresh the private index

```sh
python3 scripts/library.py index --workers 4
python3 scripts/library.py index --source odkrywamy
```

The full command inventories all PDFs and MP3s recursively, hashes every file,
uses `pdfinfo` for page counts, and runs `pdftotext -f N -l N -layout ... -` once
per uncached PDF page. Audio durations come from `ffprobe`, using at most four
workers by default (`--workers` accepts 1–8). It does **no OCR**. A source-only
refresh updates selected PDF records and retains the other catalogue records;
run the full command after adding, moving, or removing source files.

Persistent caches are keyed by the complete source SHA-256:

```text
reference-materials/.derived/<sha256>/manifest.json
reference-materials/.derived/<sha256>/text/0001.txt
reference-materials/.derived/<sha256>/ocr/0033.txt
```

The manifest records quality for each page. Interrupted text extraction resumes
from checkpoints; identical sources reuse cached pages and audio durations.
Changed content gets a separate cache, without deleting previous derivatives.
`pages`, `search`, and source-specific `inspect` rehash the original and reject
stale catalogue/cache combinations before returning content. The summary-only
`inspect` reads catalogue metadata without checking all source files.

OCR streams **one page at 110 dpi** from MuPDF into Tesseract `pol+eng`, with no
temporary image files. It caches text and word-confidence diagnostics. Repeated
requests reuse the same OCR profile. OCR updates the private manifest immediately;
run `index --source ID` to refresh its tracked catalogue summary afterward.

Quality labels are `empty`, `watermark-only`, `sparse`, `suspect-garbled`,
`extraction-error`, and `usable-unverified`. Heuristics check text quantity,
known watermarks, broken glyphs/encoding and fragmented text; OCR additionally
flags mean word confidence below 65 or more than 35% of words below 50.
These checks can miss errors or reject legitimate exercises. Even a usable page
can have wrong diacritics, lost columns, broken tables, or missing passages.
Visually verify the specific page before quoting forms or relying on a table.
Nothing generated by this tooling is marked as reviewed.

`printed_page_mapping` is null until manually verified. If needed, add individual
references to that field, for example an array of objects with `pdf_page`,
`printed_page`, and `evidence` fields. Check the visible label on each cited
page. The index preserves mappings for the same hash and clears them when the
source changes. Never infer a global printed-page offset from one observation.

## Tools and local viewing

Resolution order: `LIBRARY_PDFINFO`, `LIBRARY_PDFTOTEXT`, `LIBRARY_MUTOOL`,
`LIBRARY_TESSERACT`, or `LIBRARY_FFPROBE` override for the corresponding tool;
otherwise `PATH`; otherwise an existing `/nix/store/*-PACKAGE-*/bin/TOOL` match.
Store hashes are not hard-coded. Overrides must name an executable, not a shell
command with arguments. No tool installation is performed by the script.

If tools are missing, a temporary shell can supply them:

```sh
nix-shell -p poppler_utils mupdf tesseract ffmpeg
tesseract --list-langs
```

OCR needs both `pol` and `eng` language data in that Tesseract environment.
The existing `devenv.nix` only supplies Python/Anki dependencies.

For a visual check, use a local PDF viewer or serve this repository locally:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory /home/roverp/Documents/polish
```

Open `http://127.0.0.1:8000/reference-materials/`, select the original PDF, and
navigate to the requested PDF page (`#page=33` where the viewer supports it).
Relative links into `reference-materials/` work only when those private files
are available on that local server. They are ignored by Git and are not deployed
with GitHub Pages. This CLI does not copy source PDFs, audio, or extracted text
into public assets.
