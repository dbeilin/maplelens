# Training spot card — design

Issue: [#45](https://github.com/or-keren/maplelens/issues/45) "When clicking on the
training spots, show the mobs and a preview of the map".

Mockup: <https://claude.ai/artifact/GQPQ9149gqNsDVNu7rMn9W> (real data: a Bowman at Lv 22,
the guide's three spots).

## Why

The Class tab lists up to three training spots, and a click starts the path arrow there.
Today a spot says only its name and the monsters' level range, so the player can't tell
what the map looks like or what lives there without leaving the game to look it up. The
card answers that before they set off.

## Goals

- **Hovering a training spot shows a card** beside the box (owner picked hover over
  opening it in the box): the map's name and street, a picture of the whole map with each
  monster's spawn spots marked, and one line per monster with its picture.
- **A click still goes straight there**, as today: the card adds nothing to the click.
- **Monster pictures** (owner): each monster line leads with the monster's picture.
- **Data for every map, not only training spots** (owner: "so we could extend it later"):
  every map and monster OSMS has for the maps in `data/maps.json` ships with the app,
  though only the training spots show a card for now.

## Non-goals

- **Measuring respawns from the screen** (owner: "no need to measure ourselves").
- **A card anywhere but the Class tab's training spots**: not the job-advance row, the
  milestone rows, the Path tab's search list, or the Quests tab. The data allows them
  later; each is its own change.
- **"Dense / normal / sparse"** from OSMS's `mob_rate`: it sits between 0.6 and 1.3 on
  every training map and its in-game effect isn't known, so it isn't shown or shipped.
- **Fetching anything at runtime.** Everything ships with the app.

## Anti-goals

- The card must never take the game's keyboard or focus, and never block a click on the
  box: it shows without activating and lets the mouse through.
- A card that lingers after the mouse has left, or flickers while moving down the list.

## Approaches (owner picked C)

- **A. Open in the box**, like quest rewards: a click opens details under the spot with a
  Go button. Stays while you read and compare, but going takes two clicks and the picture
  is only as wide as the box (a tall map shows tiny).
- **B. A separate window** beside the box, opened by a click, like the EXP history: room
  for a big picture, but its own placement and closing, and one more window to manage.
- **C. A hover card** beside the box. **Chosen.** One click to go, as today, and a bigger
  picture; it's gone when the mouse leaves, so no comparing two spots side by side.

## The card

```
┌─────────────────────────────┐   ┌ box ─────────────────┐
│ Transfer Area               │   │ EXP Path Class Quests│
│ Kerning City Subway         │   │ Bowman Lv 22    3 AP │
│ ┌─────────────────────────┐ │   │ Train here · click…  │
│ │  map picture, with a    │ │   │ Tree Dungeon, For… › │
│ │  coloured dot on every  │◄├───┤▌Transfer Area     › │ (hovered)
│ │  spawn spot             │ │   │ Line 1 <Area 1>    › │
│ └─────────────────────────┘ │   └──────────────────────┘
│ [pic] Stirge                │
│  •    Lv 20 · 296 HP · 37 EXP│
│       38 spawn spots        │
│ Up to 16 monsters at once   │
└─────────────────────────────┘
```

- **Title:** the map's name; under it, in grey, its street.
- **Picture:** OSMS's full map picture (not our minimap: OSMS's spawn positions are
  pixels on its full picture, and on our minimaps they land off the platforms; the full
  picture is also far easier to read). Scaled to fit the card, kept in proportion. A dot
  on every spawn spot, in the colour of that monster's line.
- **Monster lines**, most spawn spots first: the monster's picture on a dark square with
  its dot colour in the corner; the name in bold; `Lv 20 · 296 HP · 37 EXP`; `38 spawn
  spots`.
- **`Up to N monsters at once`** (OSMS `mob_capacity`), when known.
- **`Respawns every 60 s`** on a monster line, only when OSMS gives that monster a timer on
  this map (one training map today: Malady on The Forest of Evil II). OSMS marks an
  assumed default of 7.56 s, which its own site hides; hide it too. A range
  (`10.00-20.00 [14.00]`) shows as `10–20 s`. Minutes from 120 s up (`every 5 min`).
- **Nothing to show:** a map with no picture shows the card without one; a map with no
  spawn data shows no monster lines. A spot whose map has neither shows no card.
- **Look:** the box's own (`overlay.py`): its fill, edge, fonts, label grey and value
  white. Dot colours: a short fixed list (the mockup's yellow and blue first) that reads on
  dark map art; assigned in the order the lines are listed.

## Behaviour

- Shows when the mouse enters a training spot row; hides when it leaves the row, the tab
  changes, the box is hidden (Hide / Show), the box is dragged, or the rows redraw for a
  different set of spots.
- **No flicker** *(my call)*: moving from one spot straight to the next swaps the card's
  content in place instead of hiding and re-showing it; a short delay (about 150 ms) before
  the first show, so sweeping the mouse across the tab doesn't flash it.
- **Placement:** left of the box, its top level with the hovered row, kept inside the
  screen the box is on; when there's no room on the left, it goes on the right.
- **Size** *(my call)*: about 300 px wide, the picture at most about 240 px tall, the card
  as tall as its content.
- A top-level window like `HistoryWindow` (`exp_meter/ui.py`): `Qt.Tool`, frameless, stays
  on top, shows without activating, takes no focus, ignores the mouse, not quitting the
  app on close; `native_setup` on show so it's a panel on the Mac.

## Data

### What ships

- **`src/maplelens/data/monsters.json`** *(name my call)*, for every map in `maps.json`
  that OSMS has, and every monster that spawns on one:
  - monsters by id: name, level, HP, EXP;
  - maps by our 9-digit id: the monster cap; the picture's size; spawn spots as
    `{mob, x, y}` in the shipped picture's pixels; respawn timers by monster, when OSMS has
    one.
- **`src/maplelens/data/map_pictures/<map id>.<ext>`**: OSMS's full map picture, without
  dots (dots are drawn at runtime, so later uses can mark one monster, or none). About 334
  files. Downscaled so the longest side is about 600 px; the whole folder must stay under
  about 10 MB. Format is the builder's call: one Qt reads in the frozen app on both
  platforms with no new dependency (check the `imageformats` plugins the specs keep).
- **`src/maplelens/data/monster_icons/<monster id>.png`**: OSMS's monster picture, as
  served (about 89 files, about 2 KB each).

### Where it comes from

A one-off conversion outside the repo, as for `quests.json` and the item icons, fetched
politely (an identifying user agent, a pause between requests), and committed. From
**OSMS Data Explorer** (CC BY 4.0, already credited):

- `https://osmsdataexplorer.com/data/current/maps.json`: `mob_capacity`, `mob_positions`
  (`{id, x, y}`, pixels on the full map picture).
- `https://osmsdataexplorer.com/data/current/monsters.json`: `name`, `level`, `hp`,
  `exp`, `thumbnail` (a hash), `maps[]` with `count` and an optional `mob_time`.
- `https://osmsdataexplorer.com/data/current/map_manifest.json`: map id → picture hash;
  the picture is `https://osmsdataexplorer.com/data/maps/<hash>.webp`.
- Monster pictures: `https://osmsdataexplorer.com/data/images/monsters/<thumbnail>.png`.

OSMS map ids are numbers; ours are 9-digit strings (`str(id).zfill(9)`). Spawn positions
scale with the picture.

### Data checks (tests)

Every training spot's map has an entry; every monster id in a map's spawns has a monster
entry and an icon file; every map with spawns has a picture; spawn spots lie inside the
picture.

## Code

- **Data loading:** in `tools/class_helper/data.py` *(my call)*, the one tool that uses it
  now. When a second tool wants it, it moves to a shared module then.
- **Card logic, pure** (`plan.py` or a small new module): from a map id and the data, the
  card's title, street, monster lines (sorted, with their text and dot colour), cap line,
  and the dots in picture pixels. Timer formatting here. Tested without Qt.
- **The card widget and its hover** (`tools/class_helper/ui.py`): `overlay.Row` gets a way
  to report the mouse entering and leaving (an optional callback, or the tool watches the
  rows' events; builder's call). Qt's enter and leave events are enough on both platforms:
  the box gets them on the Mac while the game is the active app (owner checked, 2026-11-14:
  rows' tooltips and hand cursor show there), so no cursor polling. Pictures load once per
  id (cached `QPixmap`).
- **Build:** the two new folders ship in both the Windows and Mac builds; add them to
  `COUNTED` in `scripts/build_installer.py` so a bundle missing them fails the check.
- **Credits:** README and `packaging/windows/NOTICE.txt`: map pictures, monster pictures
  and monster stats from OSMS Data Explorer (CC BY 4.0), next to the existing OSMS lines.
- **AGENTS.md Layout:** the new data file and folders.

## Done means

- Hovering each training spot shows its card left of the box (right, when the box is at
  the screen's left edge); leaving hides it; a click still starts the path at once.
- The card never takes focus from the game and never blocks a click on the box.
- Tests: data checks; card logic for a map with two monsters, a map with a timer (range
  and plain), a map without spawn data, a map without a picture; a UI test that hovering a
  row shows the card with the right title, and leaving hides it.
- `uv run pytest`, `uv run ruff check`, the screen-only guard pass.
- Checked by eye on a screenshot: a wide map (Line 1), a tall map (Tree Dungeon IV), a map
  with two monsters, on Windows; the card on the Mac if one is to hand.
- The frozen build (`--freeze-only`) contains both new folders and draws a map picture.

## Left to the builder

The JSON schema; the picture format and exact size; the dot list and size; the card's
margins; how `Row` reports hover; the exact show delay.
