# README for players Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite README.md so a MapleStory Classic player sees in ~10 seconds what MapleLens does, that it's safe, and where to download it.

**Architecture:** Docs only. One file rewritten (`README.md`), plus a check that its links and images resolve. No code changes.

**Tech Stack:** GitHub-flavoured Markdown; pytest (`tests/test_docs.py`).

**Spec:** `docs/superpowers/specs/2026-11-14-readme-for-players-design.md`

## Global Constraints

- Reader: a player deciding whether to download. No developer detail above "Run from source".
- Every player-facing feature on `main` (v0.6.3) mentioned briefly; no claim the code doesn't back.
- Keep the existing voice: plain, short sentences, UI names in **bold**, `•••` for the menu button.
- Keep every NiaDB guide link: `tests/test_docs.py::test_readme_credits_each_guide_page` checks them.
- Keep the meowdb and OSMS (CC BY 4.0) credit lines.
- Reuse the four screenshots in `docs/screenshots/`; no new images.
- Work on branch `claude/readme-for-players` off `main`; never touch `version` in `pyproject.toml`.

## Review Focus

- A bullet describes a feature that's on a branch but not on `main` → reader is misled. Each bullet is checked against code in Task 1.
- A relative link or image path breaks after the reorder → broken image on GitHub. Task 2 Step 3 checks every path.
- The download link points at a page that isn't `releases/latest` → player lands on an old version.
- A credit line or guide link dropped while moving Status → license / permission breach; caught by `test_docs.py` and the Task 2 grep.
- Mac-only or Windows-only behaviour stated as universal (tray vs menu bar, borderless) → wrong instructions for half the readers.

---

### Task 1: Confirm each feature bullet against the code

**Files:**
- Read: `src/maplelens/tools/*/ui.py`, `src/maplelens/tools/exp_meter/text.py`, `src/maplelens/overlay.py`, `src/maplelens/app.py`
- Create (scratch, not committed): notes in the executor's own context

- [ ] **Step 1: For each bullet in the spec's "The layout (B)" §4 and §5, find the code that does it** (grep the commit subjects listed below, then the UI strings). Record the UI wording the app actually shows (button and tab names, "measuring", "Closest" / "Best", "Pin").
  Commits to start from: `0a61764` hover card, `b21d0d6` quest rewards, `5ff6150` / `7cd7330` session average and totals, `c0cf402` measuring, `87c31da` amber warning, `0fd75c6` build choice, `4959b20` NPC on goal map, `838d5e4` hidden portal hint, `3b04232` corner resize.
- [ ] **Step 2: Drop or reword any bullet the code doesn't back.** Expected: a list of bullets per tool, each with the exact UI words.

### Task 2: Rewrite README.md

**Files:**
- Modify: `README.md` (whole file)
- Test: `tests/test_docs.py`

- [ ] **Step 1: Create the branch**

```bash
git switch -c claude/readme-for-players
```

- [ ] **Step 2: Rewrite README.md in the spec's section order:**
  1. title + pitch (as today) + `**[Download for Windows or Mac](https://github.com/or-keren/maplelens/releases/latest)**`;
  2. hero image;
  3. `## Safe to use`: the three "never"s, kept short;
  4. `## What it does` with `### Path arrow`, `### EXP meter`, `### Class helper`, `### Quest helper`: one-line pitch, 3–4 bullets from Task 1, existing screenshot and alt text;
  5. one short paragraph on the box (drag, widen from the corner, `•••`, tray on Windows / menu bar on the Mac);
  6. `## Requirements`, `## Download (Windows)`, `## Download (Mac)`: unchanged text;
  7. `## Coming next`: prices;
  8. `## Run from source (macOS, developers)` (unchanged), `## Development` (+ the guard-script sentence from today's promise section), `## Credits` (today's Status block without the "Phase 3" paragraph), `## Disclaimer`, `## License`.
  Remove `## Roadmap` and `## Status`.

- [ ] **Step 3: Check links, images and credits**

Run: `uv run pytest tests/test_docs.py -q`
Expected: all pass.

Run (bash): `grep -oE '\]\((docs/[^)]+|LICENSE|CONTRIBUTING.md)\)' README.md | sed -E 's/^\]\(|\)$//g' | xargs -I{} test -e {} && echo ok`
Expected: `ok`.

Run (bash): `grep -c 'meowdb.com/msclassic/guides/' README.md` → `15`; `grep -c 'osmsdataexplorer.com' README.md` → `2`.

- [ ] **Step 4: Full checks**

Run: `uv run pytest -q; uv run ruff check; uv run python scripts/check_screen_only.py`
Expected: all pass.

- [ ] **Step 5: Commit (with the spec and this plan)**

```bash
git add README.md docs/superpowers/specs/2026-11-14-readme-for-players-design.md docs/superpowers/plans/2026-11-14-readme-for-players.md
git commit -m "docs: README for players deciding to download"
```
