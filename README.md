# Nauka polskiego

Static HTML course: lessons and reference sheets. Served as-is by GitHub Pages.

## Deploy

1. Push this repo to GitHub.
2. Settings → Pages → Source: **Deploy from a branch** → `main` / `/ (root)`.
3. Every push republishes the site. No build step, no Actions.

## Adding a lesson

1. Create `lessons/0002-....html` (or a `reference/` sheet).
2. Link only the matching public stylesheet: `../assets/lesson.css` for lessons or `../assets/reference-page.css` for reference sheets.
3. Keep the body classes `pico lesson-page` or `pico reference-page`. Add reusable presentation rules through the matching CSS entry point, never directly in lesson HTML.
4. Commit. The pre-commit hook regenerates `index.html` and validates every page.

## CSS architecture

Page HTML links one public entry point. Each entry point loads Pico's conditional build into the low-priority `pico` cascade layer, then loads course tokens and components into the higher-priority `course` layer. This makes course components override Pico by architecture instead of selector-specificity tricks.

- `assets/lesson.css` - lessons
- `assets/reference-page.css` - printable reference sheets
- `assets/index.css` - generated index
- `assets/theme.css` - shared design tokens
- `assets/style.css` and `assets/reference.css` - implementation styles imported by their public entry points

Run `python3 scripts/check-pages` to reject direct vendor imports, inline page CSS, missing body contracts, or incorrect entry points.

## Git hooks

The pre-commit hook regenerates the index from `lessons/` and `reference/`. Enable it once per clone:

```sh
scripts/setup-git-hooks
# or: git config core.hooksPath .githooks
```

`git commit --no-verify` and GitHub web edits skip the hook, so the index can go stale after those. Run `scripts/build-index` manually to fix.
