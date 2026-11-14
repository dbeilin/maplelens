# Training Spot Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hovering a training spot in the Class tab shows a card beside the box with the map's picture, its monsters (with pictures) and their spawn spots; a click still goes straight there.

**Architecture:** A one-off conversion (outside the repo) turns OSMS's map, monster and picture data for every map we know into `data/monsters.json`, `data/map_pictures/` and `data/monster_icons/`. `class_helper/data.py` loads it; a pure `spot_card()` in `class_helper/plan.py` turns a spot into the card's text, colours and dots; `class_helper/ui.py` shows it in a frameless, non-activating top-level `SpotCard`, driven by a new hover callback on `overlay.Row`.

**Tech Stack:** Python 3.12, PySide6 (Qt 6, incl. its `qwebp` image plugin), OpenCV (conversion only, already a dependency), pytest.

**Spec:** `docs/superpowers/specs/2026-11-14-training-spot-card-design.md`

## Global Constraints

- Screen-reading only: nothing here touches the game; `uv run python scripts/check_screen_only.py` passes.
- No new dependency. Nothing fetched at runtime: every picture and number ships with the app.
- The card never takes focus or the keyboard and never blocks a click on the box.
- Data source: OSMS Data Explorer (CC BY 4.0). Fetch politely: user agent `MapleLens data conversion (github.com/or-keren/maplelens)`, 1 s between requests.
- OSMS monster ids (small ints like `9`) are their own id space, not the game ids `quests.json` uses. Never mix them.
- `data/map_pictures/` stays under 10 MB in total.
- Never change `version` in `pyproject.toml`.
- Copy: `Up to {n} monsters at once`, `{n} spawn spots` / `1 spawn spot`, `respawns every …`, `Lv {level} · {hp:,} HP · {exp:,} EXP`.

## Review Focus

- **A box at the screen's left edge, or a spot low on the screen**: the card flips to the box's right and stays fully on screen → `test_card_spot_flips_right_and_stays_on_screen` (Task 4).
- **The rows redraw while a spot is hovered** (a new EXP rate, a level-up): the card hides, and a pending show never fires on the deleted row → `test_redraw_hides_the_card_and_cancels_a_pending_show` (Task 4).
- **The tab switches or the box is hidden while hovering**: the card goes with it → `test_hiding_the_tab_hides_the_card` (Task 4).
- **Sweeping the mouse quickly across the spots**: no card flashes → `test_a_quick_pass_shows_no_card` (Task 4).
- **A map with more monsters than dot colours**: colours repeat in order, nothing crashes → `test_dot_colours_repeat_past_the_list` (Task 2).

---

### Task 1: The data, shipped

**Files:**
- Create (by the conversion, outside the repo, not committed): a script in a temp folder.
- Create: `src/maplelens/data/monsters.json`, `src/maplelens/data/map_pictures/<map id>.webp`, `src/maplelens/data/monster_icons/<osms monster id>.png`
- Modify: `src/maplelens/tools/class_helper/data.py` (loader)
- Modify: `scripts/build_installer.py` (`COUNTED`, `check_bundle`, `REQUIRED`, `MAC_REQUIRED`)
- Modify: `README.md:169`, `packaging/windows/NOTICE.txt:14`, `AGENTS.md` (Layout)
- Test: `tests/test_spot_data.py` (new), `tests/test_build_installer.py`

**Interfaces:**
- Produces, in `class_helper/data.py`:
  - `SPOTS = data/"monsters.json"`, `PICTURES = data/"map_pictures"`, `ICONS = data/"monster_icons"`
  - `@dataclass(frozen=True) class Monster: name: str; level: int; hp: int; exp: int`
  - `@dataclass(frozen=True) class MapSpawns: size: tuple[int, int]; cap: int | None; spawns: tuple[tuple[str, int, int], ...]; respawn: dict[str, tuple[float, float]]` — spawns are `(monster id, x, y)` in the shipped picture's pixels; `respawn` is monster id → (shortest, longest) seconds.
  - `@dataclass(frozen=True) class SpotData: maps: dict[str, MapSpawns]; monsters: dict[str, Monster]; pictures: Path; icons: Path` with `picture(map_id: str) -> Path | None` and `icon(monster: str) -> Path | None` (the file when it exists).
  - `@cache def load_spots(path: Path = SPOTS, pictures: Path = PICTURES, icons: Path = ICONS) -> SpotData`

`monsters.json` layout (compact, `sort_keys=True`):

```json
{"maps": {"010003062": {"size": [558, 600], "cap": 16,
                        "spawns": [["12", 140, 210], ...], "respawn": {"12": [60, 60]}}},
 "monsters": {"12": {"name": "Stirge", "level": 20, "hp": 296, "exp": 37}}}
```

`cap` and `respawn` are left out when OSMS has none; `spawns` is always there (maybe empty).

- [ ] **Step 1: Run the conversion** (a script in a temp folder; run any Python that reads the downloads with `-I`). It:
  1. Downloads `https://osmsdataexplorer.com/data/current/{maps,monsters,map_manifest}.json`.
  2. Keeps every map that is in our `src/maplelens/data/maps.json` and has a manifest hash (about 334). OSMS ids are numbers: ours are `str(id).zfill(9)`.
  3. For each: downloads `https://osmsdataexplorer.com/data/maps/<hash>.webp`, scales it with `cv2.INTER_AREA` so its longest side is at most 600 px (never up), writes `map_pictures/<id>.webp` at WebP quality 80. `size` is the written size; each `mob_positions` entry `{id, x, y}` becomes `[str(id), round(x*k), round(y*k)]`. `cap` is `mob_capacity`.
  4. `respawn`: from `monsters.json`, each monster's `maps[]` entry for this map with a `mob_time`. `"60.00"` → `[60, 60]`; `"10.00-20.00 [14.00]"` → `[10, 20]`. Leave out any that contains `7.56` (OSMS's assumed default, which its own site hides).
  5. `monsters`: every monster id found in any kept map's spawns: `name`, `level`, `hp`, `exp`. Downloads its picture `https://osmsdataexplorer.com/data/images/monsters/<thumbnail>.png` to `monster_icons/<id>.png` as served.
  6. Prints the total size of `map_pictures/`. Over 10 MB: rerun with 520 px.

  Expected: about 334 pictures, about 89 icons, under 10 MB.

- [ ] **Step 2: Write the data checks** in `tests/test_spot_data.py`, against the real files:

```python
def test_every_training_spot_has_spawn_data():
    spots, classes = load_spots(), load()
    ids = {t.place.map_id for p in classes.jobs.values() for t in p.training if t.place.map_id}
    assert ids and ids <= spots.maps.keys()


def test_every_spawning_monster_has_stats_and_a_picture():
    spots = load_spots()
    for m in spots.maps.values():
        for mob, _, _ in m.spawns:
            assert mob in spots.monsters and spots.icon(mob), mob


def test_every_map_with_spawns_has_a_picture_and_they_lie_inside_it():
    spots = load_spots()
    for map_id, m in spots.maps.items():
        if m.spawns:
            assert spots.picture(map_id), map_id
        assert all(0 <= x <= m.size[0] and 0 <= y <= m.size[1] for _, x, y in m.spawns), map_id


def test_map_pictures_stay_under_10_mb():
    assert sum(p.stat().st_size for p in PICTURES.glob("*.webp")) < 10_000_000


def test_qt_reads_a_map_picture(qapp):  # the qwebp plugin is there
    from PySide6.QtGui import QPixmap

    path = next(PICTURES.glob("*.webp"))
    assert not QPixmap(str(path)).isNull()
```

  (`qapp`: set `QT_QPA_PLATFORM=offscreen` and make a `QApplication`, as `tests/test_class_ui.py`'s `make` fixture does; use a local fixture.)

- [ ] **Step 3: Run them to see them fail**: `uv run pytest tests/test_spot_data.py -v`. Expected: FAIL, `load_spots` not defined.

- [ ] **Step 4: Implement the loader** in `class_helper/data.py` (interfaces above). Monster ids and map ids stay strings; `respawn` values become tuples.

- [ ] **Step 5: Run them to see them pass**: `uv run pytest tests/test_spot_data.py -v`. Expected: PASS.

- [ ] **Step 6: Make the build count the new folders.** In `scripts/build_installer.py`: `COUNTED` gains `"data/map_pictures"` and `"data/monster_icons"`; `check_bundle` counts every file (`p.is_file()` over `rglob("*")`), not only `*.png`, and its message says `files`, not `PNGs`; `REQUIRED` gains `"_internal/PySide6/plugins/imageformats/qwebp.dll"` and `MAC_REQUIRED` gains `"Contents/Frameworks/PySide6/Qt/plugins/imageformats/libqwebp.dylib"` (without the plugin the pictures don't load). Add `test_check_bundle_counts_map_pictures` to `tests/test_build_installer.py`: `data/map_pictures/a.webp` in src and bundle passes, removed from the bundle fails with `match="map_pictures"`. Keep the existing tests passing (their `REQUIRED` lists now include the plugin).

- [ ] **Step 7: Credits and layout.**
  - `README.md:169` and `NOTICE.txt:14` become `Minimap and map pictures, item icons, monster pictures and stats, and portal types from OSMS Data Explorer (…) (CC BY 4.0).`
  - In `AGENTS.md` Layout, after the `data/maps.json` line, add: `data/monsters.json` — each map's monster cap, spawn spots and respawn timers, and monster stats (OSMS ids); `data/map_pictures/`, `data/monster_icons/` — their pictures.

- [ ] **Step 8: Run everything**: `uv run pytest`, `uv run ruff check`, `uv run python scripts/check_screen_only.py`. Expected: all pass.

- [ ] **Step 9: Commit** the data, the loader, the tests, build and docs: `feat: map pictures, spawn spots and monster stats from OSMS (#45)`.

---

### Task 2: The card's content (pure)

**Files:**
- Modify: `src/maplelens/tools/class_helper/plan.py`
- Test: `tests/test_spot_card.py` (new)

**Interfaces:**
- Consumes: `Place` (`data.py`: `map_id`, `name`, `title` = `"Street / Name"` or None), `SpotData`, `MapSpawns`, `Monster` (Task 1).
- Produces, in `plan.py`:
  - `DOT_COLOURS = ("#ffcc33", "#7fa8ff", "#8ce678", "#ff8cc8")`
  - `CAP = "Up to {} monsters at once"`
  - `@dataclass(frozen=True) class CardMob: id: str; name: str; stats: str; spots: str; colour: str`
  - `@dataclass(frozen=True) class Card: title: str; street: str; picture: Path | None; size: tuple[int, int]; mobs: tuple[CardMob, ...]; cap: str | None; dots: tuple[tuple[int, int, str], ...]` — dots are `(x, y, colour)` in picture pixels.
  - `respawn_text(lo: float, hi: float) -> str`
  - `spot_card(place: Place, spots: SpotData) -> Card | None`

Rules: `title` is `short_name(place.name)`; `street` is the part of `place.title` before `" / "`, or `""`. Monsters most spawn spots first, ties by name; colour `DOT_COLOURS[i % len]` in that order. `stats` = `Lv {level} · {hp:,} HP · {exp:,} EXP`; `spots` = `{n} spawn spots` (`1 spawn spot`), plus ` · respawns every …` when the map has a timer for it. `respawn_text`: minutes when `lo >= 120`, else seconds; `every 60 s`, `every 10–20 s`, `every 5 min`, `every 3–30 min` (en dash; whole numbers print without decimals, others with `:g`). No map id, no map entry, or neither picture nor spawns: `None`. A spawn whose monster isn't in `monsters` is skipped.

- [ ] **Step 1: Write the failing tests** in `tests/test_spot_card.py`, with a hand-built `SpotData` (`tmp_path` pictures folder; touch `000000001.webp` for the picture):

```python
def test_card_lists_monsters_most_spots_first_with_matching_dots(tmp_path): ...
    # map 000000001: spawns 2 Snail at (10,10),(30,10), 1 Blue Snail at (20,15); cap 5
    c = spot_card(Place("000000001", "Victoria Road / Snail Field", "Victoria Road / Snail Field"), spots)
    assert c.title == "Snail Field" and c.street == "Victoria Road" and c.cap == "Up to 5 monsters at once"
    assert [m.name for m in c.mobs] == ["Snail", "Blue Snail"]
    assert c.mobs[0].stats == "Lv 1 · 45 HP · 2 EXP" and c.mobs[0].spots == "2 spawn spots"
    assert c.mobs[1].spots == "1 spawn spot"
    assert c.dots == ((10, 10, "#ffcc33"), (30, 10, "#ffcc33"), (20, 15, "#7fa8ff"))
    assert c.picture == tmp_path / "000000001.webp"

def test_a_timer_shows_on_its_monster_line(tmp_path):
    # respawn {"3": (60, 60)}
    assert c.mobs[1].spots == "1 spawn spot · respawns every 60 s"

def test_respawn_text():
    assert respawn_text(60, 60) == "every 60 s"
    assert respawn_text(10, 20) == "every 10–20 s"
    assert respawn_text(300, 300) == "every 5 min"
    assert respawn_text(180, 1800) == "every 3–30 min"
    assert respawn_text(150, 150) == "every 2.5 min"

def test_no_spawn_data_keeps_the_picture(tmp_path):   # spawns (), no cap
    assert c.mobs == () and c.cap is None and c.picture

def test_no_picture_keeps_the_monsters(tmp_path):      # no file in tmp_path
    assert c.picture is None and c.mobs

def test_no_picture_and_no_spawns_is_no_card(tmp_path):
    assert spot_card(place, spots) is None

def test_a_map_we_have_no_data_for_is_no_card(tmp_path):
    assert spot_card(Place("999999999", "X", None), spots) is None

def test_dot_colours_repeat_past_the_list(tmp_path):   # 5 monsters, one spot each
    assert [m.colour for m in c.mobs] == [*DOT_COLOURS, DOT_COLOURS[0]]
```

- [ ] **Step 2: Run them to see them fail**: `uv run pytest tests/test_spot_card.py -v`. Expected: FAIL, import error.

- [ ] **Step 3: Implement** `CardMob`, `Card`, `respawn_text`, `spot_card` in `plan.py` (rules above).

- [ ] **Step 4: Run them to see them pass**: `uv run pytest tests/test_spot_card.py -v`. Expected: PASS.

- [ ] **Step 5: Commit**: `feat: the training spot card's content (#45)`.

---

### Task 3: Rows report hover

**Files:**
- Modify: `src/maplelens/overlay.py` (`Row`, ~line 160)
- Test: `tests/test_overlay.py`

**Interfaces:**
- Produces: `Row(..., on_hover: Callable[[bool], None] | None = None)`: `enterEvent` calls `on_hover(True)`; `leaveEvent` and `hideEvent` call `on_hover(False)`. Each calls the base class too. No callback: nothing changes.

- [ ] **Step 1: Write the failing test** `test_row_reports_hover` in `tests/test_overlay.py` (offscreen `QApplication`, as the file's other Qt tests do): a shown `Row("A", "", None, on_hover=seen.append)`; send `QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1))`, then `QEvent(QEvent.Leave)`, with `QApplication.sendEvent`; then `row.hide()`. Assert `seen == [True, False, False]`.

- [ ] **Step 2: Run it to see it fail**: `uv run pytest tests/test_overlay.py::test_row_reports_hover -v`. Expected: FAIL, unexpected keyword `on_hover`.

- [ ] **Step 3: Implement** the keyword and the three event handlers in `Row`.

- [ ] **Step 4: Run it to see it pass**: `uv run pytest tests/test_overlay.py -v`. Expected: PASS.

- [ ] **Step 5: Commit**: `feat: rows can report the mouse entering and leaving (#45)`.

---

### Task 4: The card on screen

**Files:**
- Modify: `src/maplelens/tools/class_helper/ui.py`
- Create: `tests/fixtures/spots_small.json`
- Test: `tests/test_class_ui.py`

**Interfaces:**
- Consumes: `load_spots`, `SpotData` (Task 1); `spot_card`, `Card` (Task 2); `Row(on_hover=…)` (Task 3).
- Produces, in `class_helper/ui.py`:
  - `CARD_W = 300`, `PICTURE_H = 240`, `GAP = 8`, `SHOW_MS = 150`, `HIDE_MS = 80`
  - `card_spot(box: QRect, row_top: int, size: QSize, screen: QRect) -> QPoint` — left of `box` by `GAP`, top at `row_top`; on the right of `box` (by `GAP`) when the left would leave `screen`; then moved up/down to stay inside `screen`.
  - `class SpotCard(QWidget)`: `fill(card: Card, spots: SpotData) -> None`, `put(row: QWidget) -> None` (moves it with `card_spot`, from `row.window().frameGeometry()`, `row.mapToGlobal(QPoint(0, 0)).y()` and the box's screen's `availableGeometry()`).
  - `ClassHelperTool(..., data=None, spots: SpotData | None = None)` — `load_spots()` when None; `app.py` needs no change.
  - A new item kind `("spot", name, sub, map_id, best, outline)` for training rows only (`_train_items`); it draws as `"row"` does, plus `on_hover`. The job-advance and milestone rows stay `"row"`.

`SpotCard` look and flags:
- Window: `Qt.Tool | Qt.FramelessWindowHint`, plus `Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus` off the Mac. `WA_ShowWithoutActivating`, `WA_TransparentForMouseEvents`, `WA_TranslucentBackground`, `WA_QuitOnClose` False. `showEvent` calls `native_setup(self)`. Fixed width `CARD_W`.
- Paints a rounded rect in `BOX_FILL` with a 1 px `EDGE` line, as the box does (`overlay.py` ~line 667).
- Content, top to bottom, 10 px margins: the title (`VALUE_PT`, white, bold); the street (`LABEL_PT`, `LABEL_COLOR`); the picture scaled to fit `CARD_W − 20` wide and `PICTURE_H` tall, in proportion, on a `FIELD` background, with a dot (radius 4, fill its colour, 1 px `#141414` outline) at each `Card.dots` point scaled the same; per monster a 48×48 `FIELD` square holding its icon scaled to fit 44 px with its colour's dot in the corner, then the name (bold, white) and `stats` and `spots` in `LABEL_COLOR`; then `cap` in `LABEL_COLOR`. Pictures and icons load once per path (a dict of `QPixmap`).

Tool behaviour:
- `on_hover(True)` on a spot: `card = spot_card(place, spots)`; None → nothing. Card visible: `fill`, `put`, stop the hide timer. Hidden: remember (card, row) and start the show timer (`SHOW_MS`); when it fires: `fill`, `put`, `show`.
- `on_hover(False)`: stop the show timer; when visible, start the hide timer (`HIDE_MS`), which hides it. Enter on another spot before then swaps in place (above).
- `_render` (when it really redraws) stops both timers, forgets the pending row and hides the card.
- The `Place` for a spot comes from the `TrainRow` already in `_train_items`; keep it with the item (e.g. as the map id → `Place` dict the tool fills while building items).

- [ ] **Step 1: Write the fixture** `tests/fixtures/spots_small.json`: map `000000001` (the small classes fixture's Rogue training map, Lv 10–15) with `size [40, 20]`, `cap 5`, spawns `["2",10,10]`, `["2",30,10]`, `["3",20,15]`, `respawn {"3": [60, 60]}`; monsters `"2"` Snail (1, 45, 2), `"3"` Blue Snail (2, 60, 3). Extend the `make` fixture: write a 40×20 picture `000000001.webp` (a filled `QImage` saved as WebP) and `2.png`, `3.png` icons into `tmp_path`, and pass `spots=load_spots(FIXTURE, tmp_path / "pics", tmp_path / "icons")`. `load_spots` is cached: call `load_spots.__wrapped__` or clear the cache, so tests don't share a `SpotData`.

- [ ] **Step 2: Write the failing tests** in `tests/test_class_ui.py`. A helper `hover(row, on)` sends `QEnterEvent`/`QEvent.Leave` as in Task 3; waits use `PySide6.QtTest.QTest.qWait`.

```python
def test_hovering_a_spot_shows_its_card(make):
    tool = make(); tool.update(R(level=12), RECT, 0)
    spot = rows(tool)[0]              # the 000000001 training row
    hover(spot, True); QTest.qWait(SHOW_MS + 100)
    assert tool._card.isVisible() and tool._card.title() == short_name(spot.name)
    hover(spot, False); QTest.qWait(HIDE_MS + 100)
    assert not tool._card.isVisible()

def test_a_quick_pass_shows_no_card(make):
    hover(spot, True); QTest.qWait(50); hover(spot, False); QTest.qWait(SHOW_MS + 150)
    assert not tool._card.isVisible()

def test_a_spot_without_data_shows_no_card(make):
    # the fixture's "Third" training row has no map id: spot_card gives None
    hover(named(tool, "Third"), True); QTest.qWait(SHOW_MS + 100)
    assert not tool._card.isVisible()

def test_hiding_the_tab_hides_the_card(make):
    ...shown...; tool.tab.hide(); QTest.qWait(HIDE_MS + 100)
    assert not tool._card.isVisible()

def test_redraw_hides_the_card_and_cancels_a_pending_show(make):
    hover(spot, True); tool._render([("info", "x")]); QTest.qWait(SHOW_MS + 150)
    assert not tool._card.isVisible()

def test_the_card_never_takes_focus_or_clicks(make):
    c = make()._card
    assert c.testAttribute(Qt.WA_ShowWithoutActivating) and c.testAttribute(Qt.WA_TransparentForMouseEvents)
    if sys.platform != "darwin":
        assert c.windowFlags() & Qt.WindowDoesNotAcceptFocus

def test_card_spot_flips_right_and_stays_on_screen():
    screen, size = QRect(0, 0, 1366, 768), QSize(300, 400)
    assert card_spot(QRect(900, 40, 238, 300), 100, size, screen) == QPoint(900 - 8 - 300, 100)
    assert card_spot(QRect(10, 40, 238, 300), 100, size, screen) == QPoint(10 + 238 + 8, 100)
    assert card_spot(QRect(900, 40, 238, 300), 600, size, screen).y() == 768 - 400
```

  `SpotCard.title() -> str` returns the title label's text (for tests). The existing `test_training_rows_click_to_go_and_best_rate` must still pass: a click still goes at once.

- [ ] **Step 3: Run them to see them fail**: `uv run pytest tests/test_class_ui.py -v`. Expected: the new tests FAIL (`_card` / `card_spot` missing); the old ones pass.

- [ ] **Step 4: Implement** `card_spot`, `SpotCard`, the `"spot"` kind and the tool's hover handling in `ui.py`.

- [ ] **Step 5: Run them to see them pass**: `uv run pytest tests/test_class_ui.py -v`. Expected: PASS.

- [ ] **Step 6: Run everything**: `uv run pytest`, `uv run ruff check`, `uv run ruff format`, `uv run python scripts/check_screen_only.py`. Expected: all pass.

- [ ] **Step 7: Commit**: `feat: hover a training spot to see its map and monsters (#45)`.

---

### Task 5: Check it for real

- [ ] **Step 1: Look at it.** Run `uv run maplelens` with the game open (or, without it, a throwaway script that builds `SpotCard`, fills it with `spot_card` for `010003061`, `010002075` and `010003062` and grabs it with `widget.grab().save(...)`). Check by eye: a wide map (Line 1 <Area 1>), a tall one (Tree Dungeon, Forest Up North IV), one with two monsters (Tree Dungeon IV); every text line fully visible; dots on the platforms; on Windows, and on the Mac if one is to hand. Fix and re-run Task 4's tests if anything is off.

- [ ] **Step 2: The frozen build**: `uv run --group build python scripts/build_installer.py --freeze-only`. Expected: the bundle check passes (it now counts both new folders and requires `qwebp`), and `dist\MapleLens\_internal\maplelens\data\map_pictures\` holds the pictures.

- [ ] **Step 3: Commit** any fixes: `fix: …`.
