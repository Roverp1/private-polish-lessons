# Nauka polskiego

Static HTML course: 20-25-minute lessons, 10-15-minute homework pages, and responsive grammar references. Served as-is by GitHub Pages.

## Anki cards

Generate the cumulative package from the canonical vocabulary file with the project-local Devenv environment:

```sh
devenv shell -- python scripts/generate-anki.py anki/vocabulary.json
```

Packages are written to `out/output.apkg`, then incremented without overwriting
existing packages. Run `devenv shell -- python scripts/generate-anki.py --help`
for the input format and image instructions.

## Deploy

1. Push this repo to GitHub.
2. Settings → Pages → Source: **Deploy from a branch** → `main` / `/ (root)`.
3. Every push republishes the site. No build step, no Actions.

## Adding a lesson

1. Read `NOTES.md` and its publication gate. Create matching `lessons/0002-....html` and `homework/0002-....html` pages (and a `reference/` page only when useful).
2. Add five cards to `anki/vocabulary.json` and generate the cumulative deck.
3. Link only the matching public stylesheet: `../assets/lesson.css`, `../assets/homework-page.css`, or `../assets/reference-page.css`.
4. Keep the matching `pico lesson-page`, `pico homework-page`, or `pico reference-page` body classes. Add reusable presentation rules through the matching CSS entry point, never directly in page HTML.
5. Apply the content and browser checks in `NOTES.md`, run `python3 scripts/check-pages`, and regenerate the index with `scripts/build-index`. The pre-commit hook also regenerates the index and validates every page when committing.

## CSS architecture

Page HTML links one public entry point. Each entry point loads Pico's conditional build into the low-priority `pico` cascade layer, then loads course tokens and components into the higher-priority `course` layer. This makes course components override Pico by architecture instead of selector-specificity tricks.

- `assets/lesson.css` - lessons
- `assets/homework-page.css` - homework
- `assets/reference-page.css` - responsive reference pages with ordinary print flow
- `assets/index.css` - generated index
- `assets/theme.css` - shared design tokens
- `assets/style.css`, `assets/homework.css`, and `assets/reference.css` - implementation styles imported by their public entry points

Run `python3 scripts/check-pages` to reject direct vendor imports, inline page CSS, missing body contracts, or incorrect entry points.

## Git hooks

The pre-commit hook regenerates the index from `lessons/`, `homework/`, and `reference/`. Enable it once per clone:

```sh
scripts/setup-git-hooks
# or: git config core.hooksPath .githooks
```

`git commit --no-verify` and GitHub web edits skip the hook, so the index can go stale after those. Run `scripts/build-index` manually to fix.
