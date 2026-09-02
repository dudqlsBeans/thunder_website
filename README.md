# Thunder Research Group — website

A static, dependency-free site. Five HTML pages, one stylesheet, one script.
No build step, no framework: open the folder on any static host and it works.

```
index.html            Home — hero, the two divisions, six research threads, news, CTA
research.html         Full research programme, division by division
people.html           PI, postdocs, students, alumni (filterable by division)
publications.html     Selected papers (filterable by division)
join.html             Openings, what to send, contact
assets/css/style.css  Design system — all tokens live at the top
assets/js/main.js     Theme toggle, nav, scroll reveal, filters, hero field
.claude/launch.json   Local preview config (python3 -m http.server 4173)
```

## Run it locally

```bash
python3 -m http.server 4173
```

Then open http://localhost:4173.

## Placeholders you must replace before publishing

Everything below is invented scaffolding so the layout reads correctly. None of it is real.

| Where | What to replace |
| --- | --- |
| All pages | The group name **Thunder** (taken from your folder name) and the wordmark |
| `index.html` → News section | All four news entries |
| `people.html` | Every name, role, blurb, avatar initials and link — including the PI |
| `publications.html` | Every paper, author list, venue and link |
| Footers, `join.html` | `contact@example.edu`, the postal address, Scholar/GitHub links |

The news, people and publications blocks are marked with HTML comments where placeholder
content begins.

## Design notes

- **Dual accent system.** The computer science division carries an ice-cyan (`--cs`), the data
  science division a warm ember (`--ds`). The pairing is used consistently: division cards,
  research row markers, publication venues, people avatars. It is the main device that makes
  "two divisions" legible without repeating the words.
- **Dark and light.** Both are first-class and hand-tuned (dark ink-black, light warm paper).
  The toggle is in the header; the choice persists in `localStorage`. All colours are CSS
  variables under `:root` and `[data-theme="light"]` — change them in one place.
- **The hero field** is a two-source wave-interference simulation drawn on a canvas, not a
  particle mesh. It is slow, low-contrast and pauses when the tab is hidden. Tune `k`, `amp`
  and the source positions in `assets/js/main.js`.
- **Texture over gloss.** A faint SVG film grain sits over the whole page, and rules are true
  1px hairlines. This is what keeps the "futuristic" side from tipping into synthetic.
- **Type.** Newsreader (serif) for display, Inter for text, JetBrains Mono for labels and
  metadata — loaded from Google Fonts, with local fallbacks in the stack.
- **Motion** is limited to a single 18px fade-up on scroll and hairline hover transitions, and
  is fully disabled under `prefers-reduced-motion`.

## Editing tips

- Adding a research thread: copy an `<article class="area cs">` block and change `cs` to `ds`
  to switch the accent.
- Adding a person or paper: copy a card and set `data-div="cs"` or `data-div="ds"` so the
  division filter picks it up.
- Section numbering (`01 / DIVISIONS`) is plain text in the markup — renumber by hand.
- The header and footer are duplicated in each HTML file (the cost of having no build step).
  If you change one, change all five; `grep -l "Research Group" *.html` finds them.
