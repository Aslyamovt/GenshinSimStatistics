# ⚔️ Genshin DPS leaders

A **Python + Gradio** application that displays a list of *Genshin Impact* teams
sorted by damage per second (DPS), with list filtering support.

Damage measurement data is fetched from the [Simpact](https://simpact.app) database.

## Features

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
- Classification of unknown characters and weapons (adding them to `objects.json`).
- Local database `cache/local_db.json` with deduplication by team composition
  (updates by `_id`; on matching composition, the record with higher damage is kept).
  Composition includes each character's `cons`, so records with the same characters
  but different `cons` values are considered distinct.
- Downloading of avatar, weapon, and artifact set images into a local cache.
- Filter sets: **All teams**, **KQMS**, **KQMS with selector**, **FTP**.
- Character filters: required and excluded.
- Team cards with DPS, images, and a link to details on gcsim.
- Pagination of the list (10/20/50 teams per page).
- Language selector: **Russian** and **English**.

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

After launching, open the address shown in the console (default `http://127.0.0.1:7860`).

## Updating data

Press the **“Update local database”** button. The application will fetch all measurements
from Simpact. If characters or weapons that are missing from the classification lists in
`objects.json` are found, a classification panel opens — select a list for each object
and press “Apply classification and continue”.

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

- builds the executable into the repository root folder as `GenshinDpsLeaders.exe`;
- ensures the runtime data needed to launch the service (`objects.json`, `README.md`,
  `LICENSE`) are present next to the `.exe`;
- removes build auxiliary artifacts (the `build/` and `dist/` folders and the generated
  `.spec` file).

Run the built `GenshinDpsLeaders.exe`. The app creates the `cache/` directory and the
local database next to the executable and opens the Gradio interface in the browser.

## Structure

```
app.py                        # entry point
genshin_dps/
  config.py                   # paths, URLs, constants
  objects_manager.py          # objects.json
  models.py                   # models/record transformations
  db.py                       # local database + merge
  downloader.py               # API fetch and asset download
  filters.py                  # selection rules and KQMS/FTP flags
  classifiers.py              # classification of unknowns
  update.py                   # update orchestration
  i18n.py                     # interface localization (RU/EN)
  ui.py                       # Gradio interface
cache/                        # local database and images
  local_db.json
  avatars/  weapons/  artifacts/
objects.json                  # classification lists