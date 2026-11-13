# Pin EXP to every tab — design

Issue #44. Small change.

## Why

A player wants to see their EXP rate while they use Path, Class or Quests. Today the box
shows one tab at a time, so leaving EXP, or the quest helper switching the box to Quests,
hides the numbers.

## Goals / non-goals

- Goal: one line of EXP at the bottom of every tab except EXP, which the player turns on.
- Non-goal: a second box, or the full EXP rows on other tabs.
- Anti-goal: numbers that look live when they aren't (stale, measuring, bar unreadable).

## Approaches

1. **A line at the bottom of the box** (picked). Small, it stays in the box the player
   already places, and it fits the box's look. Cost: other tabs grow by one line while
   the pin is on.
2. A separate small EXP box. It can sit anywhere, but it's a second overlay window to
   place and to hide and show (Mac panels too), and more clutter over the game.
3. The full EXP rows above every tab. Nothing is lost, but the box gets much taller,
   and the Path and Quests lists are already long.

## Design

- **Toggle**: a secondary button next to History on the EXP tab, reading `Pin` while off
  and `Unpin` while on. Off by default. Saved as `settings["pin_exp"]` (a new key in
  `store.DEFAULTS`).
- **The line**: `EXP  2.31%/h · Lvl in 1h 20m ›` at the bottom of the box, under the
  tab's page and above the notice line. The grey label is `EXP` and the text is white.
  It shows %/h and the time to level from the last-5-min rate. Raw EXP/h is left out:
  it doesn't fit 214 px.
- **States**: `Measuring…` while measuring or with no rate yet, `Paused` while paused,
  and `Can't read bar` in the accent colour when the bar can't be read. It is never
  blank, and never shows old numbers as if they were live.
- **Click**: opens the EXP tab.
- **Hidden** on the EXP tab itself, while the status line replaces the tabs, while About
  is open, and when the pin is off.
- **Quest auto-switch**: the line stays when the box jumps to Quests.

## Left to the builder

- How the box gets the line. A generic footer slot on `Box` that the EXP tool fills is
  the likely shape: tools must stay independent, so the box mustn't know about EXP.
- The line's text as a pure function next to `box_lines` in `exp_meter/text.py`, tested
  the same way.
