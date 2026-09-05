# Notes

## New-session bootstrap
- Activate the `teach` skill before continuing this course.
- Read `MISSION.md`, `CURRICULUM.md`, `RESOURCES.md`, every file in `learning-records/`, and this file.
- Read `anki/vocabulary.json` before selecting new vocabulary.
- Before authoring a page, inspect the latest active lesson/homework and shared assets. Reuse them; do not invent a second design system.
- Only the next lesson is authored as active course material. Later curriculum titles may be refined without removing required targets.
- Add a learning record only after evidence of understanding. Coverage is not learning.

## Learner profile
- Programmer; systematic thinker; wants the full Polish grammar system, theory from zero
- Has lived in Poland 3+ years; historically used Polish mainly for transactions (shops, banks)
- Took a pre-move group course advertised as B2; actual outcome was about A2
- Learns better when grammar is presented as a system, with reasons, algorithms, examples, and immediate practice
- User's stalls were a tools and activation-loop problem, not a discipline problem

## Baseline (self-reported, not a placement certificate)
- Solid A2 overall
- Can order food, buy things, read a short news article, and describe the day with vocabulary gaps
- Can handle a doctor visit only after preparing vocabulary
- Cannot comfortably follow two native speakers chatting at normal speed
- Strongest: receptive reading; weakest: real-time listening; productive speech has vocabulary gaps
- Skip alphabet/pronunciation review unless later evidence shows a gap
- Previous voice lessons exposed the learner to grammar labels but did not teach the underlying rules. Do not import their classifications as mastery or error evidence.

## Time and budget
- 15-60 min/day
- Max $25/month for paid tools; no human-tutor budget
- Do not push the human-tutor path unless the user changes the budget or asks

## Delivery workflow
- The learner reads each lesson, writes the specified notebook entry, and completes each exercise before reading the next rule.
- Closed exercises reveal answers for roughly 30-50% of their items. Revealed answers explain the rule; they are practice, not assessment evidence.
- Open exercises receive an analogous model, never the learner's exact answer.
- The learner submits the unrevealed exit check and homework. Other lesson exercises are submitted when uncertain or requested.
- Review the submission, explain target errors, and request a new repair example when needed.
- Generate the next lesson only after reviewing the current submission.
- Text work can demonstrate grammatical retrieval and production. Do not claim pronunciation evidence without audio.

## Mandatory lesson structure
1. Start with why the topic matters and the communication problem it solves.
2. State observable outcomes and a clear "not today" scope boundary.
3. Teach one concept, or at most two inseparable rules, in short sections.
4. For each rule: explain its purpose, provide an exact notebook block, show a worked example, and immediately provide practice.
5. Do not introduce another rule before the practice attached to the current rule.
6. Provide a decision procedure or mental model when the topic supports one.
7. Keep new grammar examples on familiar vocabulary.
8. Introduce five deliberate vocabulary entries in a separate section after the main grammar practice.
9. End with an unrevealed exit check and a link to matching homework.
10. Cite the source used and remind the learner to ask about unclear material.

## Homework structure
- One matching page under `homework/` for every lesson
- Normally 10-15 minutes
- Progress from recognition to completion, controlled construction, one-error repair, and limited production
- Include one or two delayed-review items when earlier material is available
- Give one operation per block and specify the expected answer format
- Provide hidden answers for selected representative items only
- End with a compact submission template

## Vocabulary and Anki
- `anki/vocabulary.json` is the only vocabulary ledger; do not create a duplicate Markdown status file.
- Five entries per lesson by default, each with an immutable ID and lesson provenance.
- Front: Polish word or useful phrase.
- Back: concise Polish definition and natural Polish example.
- Grammar terminology belongs in `GLOSSARY.md` and does not count toward the five entries.
- Vocabulary has no repository mastery status. Anki owns scheduling and memorization state.
- After adding lesson vocabulary, run `python scripts/generate-anki.py anki/vocabulary.json` inside the project environment and report the package path.

## Canonical implementation
- Lesson exemplar: `lessons/0001-noun-gender-singular.html`
- Homework exemplar: `homework/0001-noun-gender-singular.html`
- Shared lesson styles: `assets/style.css`
- Shared homework styles: `assets/homework.css`
- Shared reference styles: `assets/reference.css`
- Pico baseline: `assets/vendor/pico.conditional.min.css`, loaded before custom CSS
- Future pages link existing shared assets. Extend shared assets only for genuinely reusable components.
- Keep semantic HTML: `main`, `section`, headings, tables, `details`, buttons, and accessible labels.
- Use `lang="pl"`; all user-visible course text is Polish except original source titles.

## UI quality standard
- Adult editorial study-manual style: warm paper, dark readable body text, restrained Polish-crimson accent
- Sans-serif body text for readability; serif display face only for major headings
- Wide shell, controlled prose measure, wider breakout regions for tables/exercises
- Desktop rail; mobile contents disclosure; no horizontal page overflow
- Wide tables scroll inside their own container on mobile
- Hidden answer explanations use native `details` controls and remain usable without JavaScript
- Reference sheets are dense but readable, responsive on screen, and designed for A4 printing/copying by hand
- Respect `prefers-reduced-motion`; provide dedicated print rules

## Pico CSS traps already encountered
- Pico styles semantic `article`, `code`, headings, and `summary`. Custom components using those elements need body-scoped selectors such as `body.pico.lesson-page article.component`.
- Reset Pico article margin, padding, and shadow explicitly for custom cards.
- Override Pico accordion variables (`--pico-accordion-close-summary-color`, `--pico-accordion-open-summary-color`) on custom summaries.
- Scope small heading styles under `body.pico.lesson-page h3`; otherwise Pico's 1.5rem grey heading wins.
- Scope prompt code blocks so Pico's dark inline-code theme does not leak into them.
- During browser verification, use a cache-busting query or reload after CSS edits before trusting computed styles.

## Verification before finishing a lesson
- Verify at 375px, 768px, 1024px, and 1440px.
- Check page overflow; only designated table containers may scroll horizontally.
- Check computed styles for headings, summaries, prompt blocks, cards, shadows, padding, and margins.
- Test hidden answer disclosures and keyboard focus.
- Check browser console errors.
- Check print media for the lesson and A4 reference sheet.
- Search visible lesson, homework, and reference text for accidental English, excluding bibliographic titles.

## Repository workflow
- Read `README.md` before adding pages.
- Add matching sequential files: `lessons/NNNN-slug.html` and `homework/NNNN-slug.html`; add `reference/NNNN-slug.html` only when it has durable value.
- The repository index is generated from `lessons/`, `homework/`, and `reference/` by `scripts/build-index`.
- The configured pre-commit hook regenerates `index.html`; if hooks are unavailable, run `scripts/build-index` manually.
- Keep commits atomic and conventional. Do not stage unrelated `.agents/`, `.opencode/`, or skill files.

## Communication preferences
- Be concise, direct, and sincere; no corporate filler
- Avoid em dashes
- Do not compare or recommend speaking tools unless explicitly asked
