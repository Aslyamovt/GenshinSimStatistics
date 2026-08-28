# ⚙️ Genshin Sim Statistics

A **Python + Gradio** application that combines two tools for working with *Genshin
Impact* damage measurements in one interface:

1. **Genshin DPS Leaders** — a leaderboard of teams sorted by damage per second (DPS),
   with list filtering support. Data is fetched from the [Simpact](https://simpact.app)
   database.
2. **Wfpsim database** — local storage and management of damage measurements from the
   [Wfpsim](https://wfpsim.com) service (an unofficial fork of gcsim, which uses the
   Simpact database as part of its ecosystem).

The interface supports **Russian** and **English** languages, selectable globally for
both tabs.

## Features

### Genshin DPS Leaders

- Iterative fetch of all measurements from the Simpact database (`skip` increases
  by 100 until fewer than 100 records are returned).
- Automatic filtering of records by rules:
  1. weapons from `leg_weapons_list` are forbidden;
  2. characters from `new_event_leg_names_list` with `cons > 0` are forbidden;
  3. characters from `old_event_leg_names_list` with `cons > 1` are forbidden;
  4. characters from `standart_leg_names_list` with `cons > 4` are forbidden;
  5. characters with level other than 90 are forbidden;
  6. teams with fewer than 4 characters are forbidden;
  7. characters without the `sets` field are forbidden.
- Classification of unknown characters and weapons (adding them to `cache/objects.json`).
- Local database `cache/local_db.json` with deduplication by team composition
  (updates by `_id`; on matching composition, the record with higher damage is kept).
  Composition includes each character's `cons`, so records with the same characters
  but different `cons` values are considered distinct.
- Downloading of avatar, weapon, and artifact set images into a local cache.
- Filter sets: **All teams**, **KQMS**, **KQMS with selector**, **FTP**.
- Character filters: required and excluded.
- Source filter — which records to display in the leaderboard:
  - **Only gcsim** — only Simpact records;
  - **Wfpsim for unique** — Simpact records plus Wfpsim records that have no match
    (same characters and `cons`) in the local Simpact database;
  - **Wfpsim for all** — Simpact records, unique Wfpsim records, and for compositions
    present in both sources the record with the higher DPS is shown.
- Team cards with DPS, images, and a link to details on gcsim/wfpsim.
- Records from the Wfpsim database are marked with a red **wfpsim** label and have a
  **Mark as invalid** button below the card. Pressing it sets `not_valid = True` for the
  record, so it immediately disappears from the leaderboard (and, if "Wfpsim for all" is
  active and there was a lower-damage gcsim analog, that analog is shown instead).
- Pagination of the list (10/20/50 teams per page).

### Wfpsim database

- A separate local database `cache/wfpsim_db.json` (never mixed with the Simpact
  database).
- **Add new record** — opens a dialog where you enter a link in the format
  `https://wfpsim.com/sh/{ID}` and press **Continue**. The app then fetches JSON from
  `https://wfpsim.com/api/share/{ID}`.
  - If the record has no damage measurement results in the Wfpsim database, a message
    is shown.
  - Otherwise, the JSON is converted to the same record format used by Simpact, the
    `config` field is stored additionally, and the record is saved to the local database.
- Measurement cards showing: average DPS, character names, character avatars, weapon
  icons, artifact set icons, `cons` values, and weapon `refine` values.
- Card actions:
  - **Details on wfpsim** — opens the saved record link (`https://wfpsim.com/sh/{ID}`
    by default, or the exact link entered when adding/replacing);
  - **Replace wfpsim link** — opens a dialog to enter a new link and replaces the
    record's ID and link (no new record is created);
  - **Delete measurement** — removes the record from the local database;
  - **Toggle validity status** — switches the `not_valid` flag on the record
    (`True` ↔ `False`); invalid records are hidden from the list unless the
    **Show invalid** checkbox is enabled;
  - **Copy config** — copies the record's `config` field to the clipboard.
- The list of cards can be sorted by **date added** or **DPS**, and filtered by a set
  of required characters and a set of excluded characters. Filtering uses the combined
  character lists of `cache/objects.json` and `cache/wfpsim_objects.json`.
- The **Show invalid** checkbox toggles whether records with `not_valid = True` are shown.
- Valid Wfpsim records are automatically transformed to the Simpact record format and
  stored in a separate file `cache/wfpsim_records.json` (distinct from both
  `cache/local_db.json` and `cache/wfpsim_db.json`). Adding/replacing/deleting or
  toggling validity of a Wfpsim record immediately updates the Genshin DPS Leaders tab.
- When adding/replacing a record, if it contains characters or weapons that are missing
  from the combined classification lists, a classification panel opens (analogous to the
  one in Genshin DPS Leaders). The results are written to a separate file
  `cache/wfpsim_objects.json` with the same structure as `objects.json`, so the base
  `objects.json` is never modified by Wfpsim data.
- Artifact set icons, character avatars, and weapon icons are first checked in the
  local cache, then fetched from the Simpact database (Wfpsim has no asset store of its
  own). If an artifact is missing from Simpact, `cache/default.png` is used instead.

## Installation

```bash
pip install -r requirements.txt
```

## Running

### From sources

```bash
python app.py
```

After launching, open the address shown in the console (default `http://127.0.0.1:7860`).

### From the executable (`.exe`)

No Python installation is required to run the built app:

1. Take the `GenshinSimStatistics.exe` file from the repository root.
2. Put it in a folder of your choice (it should be placed together with `objects.json`,
   `README.md` and `LICENSE`, which `build.py` places next to the `.exe`).
3. Double-click `GenshinSimStatistics.exe` (or run it from the command line). A console
   window opens, and then the Gradio interface launches in the browser at the address
   printed in the console (default `http://127.0.0.1:7860`).

On first run the app creates the `cache/` directory and the local databases
(`cache/local_db.json` for Simpact and `cache/wfpsim_db.json` for Wfpsim) next to the
executable, storing all downloaded images there.

## Updating data (Genshin DPS Leaders)

Press the **“Update local database”** button. The application will fetch all measurements
from Simpact. If characters or weapons that are missing from the classification lists in
`cache/objects.json` are found, a classification panel opens — select a list for each
object and press “Apply classification and continue”.

## Building the executable

To build a standalone Windows `.exe` (onefile), run:

```bash
pip install -r requirements.txt
python build.py
```

or, on Windows, simply:

```bat
build.bat
```

The script uses [PyInstaller](https://pyinstaller.org/) (installed automatically if missing)
and:

- builds the executable into the repository root folder as `GenshinSimStatistics.exe`;
- ensures the runtime data needed to launch the service (`objects.json`, `README.md`,
  `LICENSE`) are present next to the `.exe`;
- removes build auxiliary artifacts (the `build/` and `dist/` folders and the generated
  `.spec` file).

Run the built `GenshinSimStatistics.exe`. The app creates the `cache/` directory and the
local databases next to the executable and opens the Gradio interface in the browser.

## Structure

```
app.py                        # entry point
build.py                      # PyInstaller build script
genshin_dps/
  config.py                   # paths, URLs, constants (Simpact + Wfpsim)
  objects_manager.py          # objects.json
  models.py                   # Simpact record transformations
  db.py                       # Simpact local database + merge
  downloader.py               # Simpact API fetch and asset download
  filters.py                  # selection rules and KQMS/FTP flags
  classifiers.py              # classification of unknowns
  update.py                   # update orchestration
  i18n.py                     # interface localization (RU/EN)
  html_utils.py               # shared HTML helpers (data-URI images, DPS formatting)
  classifier_ui.py            # shared classification panel helpers
  ui.py                       # Gradio interface (tabs, global language)
  wfpsim/                     # Wfpsim database module
    models.py                 # Wfpsim JSON -> local record conversion
    db.py                     # Wfpsim local database (separate file)
    service.py                # Wfpsim API requests + asset fallback to Simpact
    records.py                # Wfpsim -> Simpact record transform + merge for DPS tab
    ui.py                     # Wfpsim tab interface
cache/                        # local databases, images and objects
  local_db.json               # Simpact database
  wfpsim_db.json              # Wfpsim database
  wfpsim_records.json         # transformed Wfpsim records for Genshin DPS Leaders
  objects.json                # base classification lists
  wfpsim_objects.json         # Wfpsim classifications (same structure as objects.json)
  avatars/  weapons/  artifacts/
  default.png                 # fallback image for missing artifacts