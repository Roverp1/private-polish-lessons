# Nauka polskiego

Static HTML course: concise lessons, matching homework, and reference sheets. Served as-is by GitHub Pages.

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

1. Create matching `lessons/0002-....html` and `homework/0002-....html` pages (and a `reference/` sheet only when useful).
2. Add five cards to `anki/vocabulary.json` and generate the cumulative deck.
3. Link only the matching public stylesheet: `../assets/lesson.css`, `../assets/homework-page.css`, or `../assets/reference-page.css`.
4. Keep the matching `pico lesson-page`, `pico homework-page`, or `pico reference-page` body classes. Add reusable presentation rules through the matching CSS entry point, never directly in page HTML.
5. Commit. The pre-commit hook regenerates `index.html` and validates every page.

## CSS architecture

Page HTML links one public entry point. Each entry point loads Pico's conditional build into the low-priority `pico` cascade layer, then loads course tokens and components into the higher-priority `course` layer. This makes course components override Pico by architecture instead of selector-specificity tricks.

- `assets/lesson.css` - lessons
- `assets/homework-page.css` - homework
- `assets/reference-page.css` - printable reference sheets
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
