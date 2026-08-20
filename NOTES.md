# Notes

## New-session bootstrap
- Activate the `teach` skill before continuing this course.
- Read `MISSION.md`, `RESOURCES.md`, every file in `learning-records/`, and this file.
- Before authoring a lesson, inspect the canonical lesson, reference sheet, and shared assets listed below. Reuse them; do not invent a second design system.
- Lesson 1 has been authored but not completed by the learner. Do not assume the case system is learned. Ask for the ChatGPT Voice end-of-lesson report or help the learner complete Lesson 1 before deciding whether to continue.
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

## Time and budget
- 15-60 min/day
- Max $25/month for paid tools; no human-tutor budget
- Do not push the human-tutor path unless the user changes the budget or asks

## Final delivery workflow (mandatory until revised)
- Lesson HTML and reference sheets are fully in controlled A2/B1 Polish. Original-language source titles are allowed.
- The user uploads the lesson HTML to ChatGPT Voice and sends the start prompt embedded in the lesson.
- ChatGPT Voice points to one short section. The learner reads it aloud and says `Skończyłem`.
- The voice teacher must then verify understanding through an open explanation, a specific checking question, and a transfer task with a new example. It must not rely on "Czy rozumiesz?".
- After understanding is demonstrated, the voice teacher assigns a short notebook note. The learner reads the note back and the teacher checks it before moving on.
- Polish is the default teaching language. If Polish clarification still fails, the learner may explicitly request one short English explanation; teaching then returns to Polish.
- Do not interrupt reading for minor pronunciation mistakes. Correct errors that block understanding or change the word. After a section, mention at most one recurring high-value pronunciation issue.
- End with closed-notes retrieval, spoken production, and a structured text report: demonstrated abilities, repeated errors with corrections, important pronunciation issues, review needs, and readiness for the next lesson.
- The learner brings that report back here. Use it as evidence for a learning record and for selecting the next lesson.

## Mandatory lesson structure
1. Start with why the topic matters and the communication problem it solves.
2. State observable outcomes and a clear "not today" scope boundary.
3. Split theory into short read-aloud sections, each teaching one manageable idea.
4. After every major section, include a collapsed `teacher-guide` with:
   - expected understanding;
   - an open comprehension question;
   - one transfer task using a new example;
   - remediation guidance for a wrong answer;
   - an exact, short notebook task.
5. Provide a decision procedure or mental model when the topic supports one.
6. Show worked examples before independent exercises.
7. Sequence practice from notes allowed to notes closed, then spoken production.
8. Include approximately 10 Anki-ready phrases taken from the lesson itself.
9. Add a printable/copyable reference sheet when it will remain useful across lessons.
10. End with a voice-teacher report schema and a next-lesson indication that remains provisional until the report is reviewed.

## Anki standard
- Around 10 entries per lesson; useful phrases or short sentences, not isolated vocabulary padding
- Front: Polish phrase
- Back: simple Polish definition + Polish example sentence + grammar trigger when relevant
- Keep back-side vocabulary around A2 level; simplify any definition the learner cannot parse
- Every phrase must reinforce the current grammar topic or a high-utility pattern from the lesson

## Canonical implementation
- Lesson exemplar: `lessons/0001-the-case-system-as-a-system.html`
- Reference exemplar: `reference/0001-case-system-cheat-sheet.html`
- Shared lesson styles: `assets/style.css`
- Shared reference styles: `assets/reference.css`
- Shared quiz behavior: `assets/lesson.js`
- Pico baseline: `assets/vendor/pico.conditional.min.css`, loaded before custom CSS
- Future lessons link existing shared assets. Extend shared assets only for genuinely reusable components.
- Keep semantic HTML: `main`, `section`, headings, tables, `details`, buttons, and accessible labels.
- Use `lang="pl"`; all user-visible interface text and quiz feedback are Polish.

## UI quality standard
- Adult editorial study-manual style: warm paper, dark readable body text, restrained Polish-crimson accent
- Sans-serif body text for readability; serif display face only for major headings
- Wide shell, controlled prose measure, wider breakout regions for tables/exercises
- Desktop rail; mobile contents disclosure; no horizontal page overflow
- Wide tables scroll inside their own container on mobile
- Quiz feedback uses text plus colour, visible keyboard focus, `aria-pressed`, disabled answered options, progress, and reset
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
- Test correct and wrong quiz answers, progress updates, reset behavior, and keyboard focus.
- Check teacher guides are present in the DOM and readable by file-analysis models.
- Check browser console errors.
- Check print media for the lesson and A4 reference sheet.
- Search visible lesson/reference text for accidental English, excluding bibliographic titles and the explicit English-fallback instruction.

## Repository workflow
- Read `README.md` before adding pages.
- Add sequential files: `lessons/NNNN-slug.html` and, when needed, `reference/NNNN-slug.html`.
- The repository index is generated from `lessons/` and `reference/` by `scripts/build-index`.
- The configured pre-commit hook regenerates `index.html`; if hooks are unavailable, run `scripts/build-index` manually.
- Keep commits atomic and conventional. Do not stage unrelated `.agents/`, `.opencode/`, or skill files.

## Communication preferences
- Be concise, direct, and sincere; no corporate filler
- Avoid em dashes
- Do not compare/recommend speaking tools unless explicitly asked; ChatGPT Voice is the selected lesson-delivery channel
