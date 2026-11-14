# README for players — design

## Why

The README's reader is a MapleStory Classic player deciding whether to download
MapleLens. Today the features merged since v0.6 are partly missing, the Roadmap and
Status are stale, and the "screen-reading only" promise sits below every screenshot.

## Goals

- In ~10 seconds a player sees what MapleLens does and that it won't get them banned.
- Every player-facing feature on `main` (v0.6.3) is mentioned, briefly.
- A one-click path to the download.

## Non-goals / anti-goals

- Not a manual: no per-button walkthroughs beyond what Download already has.
- No developer detail above the fold (guard script, CI, uv).
- No new claims the app doesn't back up; no screenshots with character names or chat.

## Approaches

- A. Keep the layout, add a sentence per new feature. Smallest diff, but dense paragraphs
  and the safety promise stays buried.
- **B. Rewrite the top half for players (picked).** Pitch, hero, download link, short
  "Safe to use", then each tool as a one-line pitch + 3–4 bullets + its screenshot.
- C. Feature table at the top. Scannable but spec-sheet-like, poor on phones.

## The layout (B)

1. Title, pitch (as today), one line: **[Download for Windows or Mac](releases/latest)**.
2. Hero screenshot (as today).
3. **Safe to use**: screen-reading only, the three "never"s, kept short. The guard
   script line moves to Development.
4. **What it does**, one subsection per tool: one-line pitch, 3–4 bullets, screenshot.
   - Path arrow: route list to any map; arrow to the next portal; leads to an NPC on the
     goal map; hidden portals get a hint.
   - EXP meter: live EXP/hour and time to level (shows from the second kill, marked
     measuring); session average and totals across maps; History per map with the best
     maps for your class and level; Pin keeps the line on every tab; amber warning when
     the EXP bar can't be read.
   - Class helper: best training spot first, one click to route there; hover a spot for
     its map, spawns and monster stats; choose your build (Beginners pick a class);
     job advancement, gear, AP/SP with marks on the game's stat and skill windows.
   - Quest helper: open a quest and see where each NPC, monster and item is; rewards and
     chain totals; follows the game's Quest Helper, targets drop off as done;
     Closest / Best per quest.
5. A short "The box" line: drag it anywhere, drag the corner to widen, ••• menu, tray /
   menu-bar icon to hide.
6. Requirements, Download (Windows), Download (Mac): unchanged in substance.
7. **Coming next**: prices.
8. Run from source, Development (+ the guard script line), Credits (today's Status
   credits, without the "Phase 3" line), Disclaimer, License.

## Left to the builder

- Exact wording; keep the existing voice (plain, short, bold UI names).
- Verify each bullet against the code before writing it; drop any it can't confirm.
- Screenshots: reuse the four existing ones. No new shots unless the owner adds them
  (`scripts/grab.py --screen`); the hover card and rewards stay text-only.
