# PRD: Team Pokémon Overview (Deck & Overview Pages)

Date: 2026-02-06

## Summary
Backport the Team Pokémon Overview UI from the experimental addon into the stable addon version (no existing team overview). The feature injects a compact, styled team grid into Anki’s Deck Browser and Deck Overview pages and is gated by a settings toggle.

## Background / Current State (Experimental)
The experimental build already includes the team overview module and integration:
- UI builder + hooks: [src/Ankimon/gui_classes/overview_team.py](src/Ankimon/gui_classes/overview_team.py)
- Hook registration via module import: [src/Ankimon/__init__.py](src/Ankimon/__init__.py)
- Settings default + config: [src/Ankimon/pyobj/settings.py](src/Ankimon/pyobj/settings.py), [src/Ankimon/config.json](src/Ankimon/config.json)
- Settings UI grouping: [src/Ankimon/pyobj/settings_window.py](src/Ankimon/pyobj/settings_window.py)
- i18n names/descriptions: [src/Ankimon/lang/setting_name.json](src/Ankimon/lang/setting_name.json), [src/Ankimon/lang/setting_description.json](src/Ankimon/lang/setting_description.json)

Stable build (folder 1908235722) lacks these files and settings.

## Goals
- Display the player’s current team as a grid (up to 6) at the top of:
  - Deck Browser (stats area)
  - Deck Overview (table area)
- Respect team order if team.json exists; fallback to mypokemon.json otherwise.
- Provide a settings toggle to enable/disable the overview.
- Fail gracefully when files/sprites are missing (no crashes).

## Non-Goals
- Team editing or swap functionality.
- New data formats or migrations beyond adding the setting key.
- Reworking deck/overview layouts beyond prepending HTML.

## User Stories
- As a learner, I want to see my current Pokémon team when browsing decks so I can quickly confirm who is active.
- As a power user, I want to disable the overview if it feels noisy.

## Functional Requirements
1. **HTML Injection**
   - Prepend team grid HTML to `content.stats` in Deck Browser render.
   - Prepend team grid HTML to `content.table` in Deck Overview render.
2. **Team Loading**
   - If team.json exists, read ordered `individual_id` values and resolve against mypokemon.json.
   - Otherwise, read mypokemon.json as-is.
   - Return empty list on errors (never raise).
3. **UI Layout**
   - Grid of max 6 Pokémon.
   - Each card shows sprite, display name (nickname preferred), level, HP, and types.
   - Optional pokéball background behind sprite.
   - Type-based background colors (single or multi-type gradient).
4. **Settings Toggle**
   - New key: `gui.team_deck_view` (default: true).
   - Shown under “Styling” settings group as “Team Overview in Deck Overview”.
5. **Compatibility**
   - No dependence on external web resources.
   - Works without breaking if any sprite file is missing.

## Data & Dependencies
- `mypokemon.json` (team data)
- `team.json` (optional ordered team file)
- `addon_files/pokeball.png` (sprite backdrop)
- Sprite resolver (same as experimental `get_sprite_path`)
- Base64 image helper (same as experimental `png_to_base64`)

## Implementation Plan (Stable Addon: 1908235722)
1. **Add module**
   - Create `gui_classes/overview_team.py` by porting from experimental.
2. **Hook Registration**
   - Import the module in `__init__.py` to register hooks when setting is enabled.
3. **Settings Defaults & Config**
   - Add `gui.team_deck_view` to `pyobj/settings.py` DEFAULT_CONFIG.
   - Add `gui.team_deck_view` to `config.json` defaults.
4. **Settings UI & i18n**
   - Add the setting to the “Styling” group in `pyobj/settings_window.py`.
   - Add name in `lang/setting_name.json`.
   - Add description in `lang/setting_description.json`.
5. **Resources & Utils**
   - Add `pokeball_path` in `resources.py` (alias `addon_files/pokeball.png`).
   - Add `png_to_base64` helper to `utils.py`.
   - Add or port `get_sprite_path` (create `functions/sprite_functions.py` or equivalent) and update imports accordingly.

## Risks / Notes
- Hook registration happens at import time; toggling the setting may require restart (current experimental behavior).
- Sprite loading uses base64; large sprites could increase HTML size but is acceptable for 6 items.
- Dark mode styling may need minor adjustments if the host UI theme conflicts with the injected CSS.

## Success Criteria
- Team grid appears at top of Deck Browser and Deck Overview when enabled.
- Toggle disables the grid completely.
- No errors when team.json or sprites are missing.

## Blocker: Missing `poke_engine` Module (Startup Crash)

**Status:** 🔴 Blocking — addon cannot load at all

**Error (Anki 25.09.2, Python 3.13.5, Qt 6.9.1, Windows 11):**
```
ModuleNotFoundError: No module named '1908235722.poke_engine.objects'
```

**Traceback:**
```
__init__.py  →  singletons.py (line 21)
  →  pyobj/collection_dialog.py (line 14)
    →  pyobj/pokemon_obj.py (line 7)
      →  from ..poke_engine.objects import Pokemon   ← FAILS
```

**Root Cause:**
`1908235722/poke_engine/` exists as a folder but is **completely empty** — no `__init__.py`, no `objects.py`, none of the sub-modules that the experimental build has under `src/Ankimon/poke_engine/`. The import `from ..poke_engine.objects import Pokemon` therefore raises `ModuleNotFoundError` and prevents the entire addon from loading.

**Impact:**
This is a **fatal startup error**. Ankimon does not load at all; the Team Overview feature (and all other functionality) is unreachable until this is resolved.

**Required Fix:**
Port the `poke_engine/` package from the experimental build into the stable addon folder. At minimum the following files are needed to unblock the import chain:

1. `poke_engine/__init__.py`
2. `poke_engine/objects.py` (defines the `Pokemon` class used by `pokemon_obj.py`)
3. Any transitive dependencies imported by `objects.py`:
   - `poke_engine/constants.py` (imported as `from . import constants`)
   - `poke_engine/data.py` (imported as `from .data import all_move_json`)

Once the `poke_engine` package is populated, the `ModuleNotFoundError` will be resolved and the addon will proceed past startup.

**Verification:**
- Launch Anki and confirm no `ModuleNotFoundError` for `poke_engine.objects`.
- Confirm singletons load successfully and the addon initialises.

---

## TODO (for another agent)
- [ ] Port `overview_team.py` into 1908235722/gui_classes/.
- [ ] Add `gui.team_deck_view` to DEFAULT_CONFIG in 1908235722/pyobj/settings.py.
- [ ] Add `gui.team_deck_view` to 1908235722/config.json.
- [ ] Add setting name/description to 1908235722/lang/setting_name.json and 1908235722/lang/setting_description.json.
- [ ] Add “Team Overview in Deck Overview” to “Styling” group in 1908235722/pyobj/settings_window.py.
- [ ] Add `pokeball_path` to 1908235722/resources.py (pointing to addon_files/pokeball.png).
- [ ] Add `png_to_base64` helper to 1908235722/utils.py.
- [ ] Add/port `get_sprite_path` utility (match experimental behavior) and update imports in overview module.
- [ ] Import `overview_team` in 1908235722/__init__.py so hooks are registered.
- [ ] Manual smoke test in Anki: open Deck Browser + Deck Overview with feature on/off.
