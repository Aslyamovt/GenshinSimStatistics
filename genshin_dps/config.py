"""Конфигурация приложения Genshin DPS leaders: пути, URL, константы."""

import sys
from pathlib import Path


def _base_dir() -> Path:
    """Корневая директория приложения.

    При запуске из исходников это папка, содержащая пакет ``genshin_dps``.
    При запуске собранного .exe — директория, в которой лежит исполняемый файл
    (туда кладутся ``objects.json``, кэш и прочие данные).
    """
    if getattr(sys, "frozen", False):  # PyInstaller onefile
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# Корень проекта (папка, содержащая пакет genshin_dps или сам .exe)
BASE_DIR = _base_dir()

# --- Пути к кэшу и файлам ---
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = CACHE_DIR / "local_db.json"
OBJECTS_PATH = BASE_DIR / "objects.json"

AVATARS_DIR = CACHE_DIR / "avatars"
WEAPONS_DIR = CACHE_DIR / "weapons"
ARTIFACTS_DIR = CACHE_DIR / "artifacts"

ASSET_DIRS = (AVATARS_DIR, WEAPONS_DIR, ARTIFACTS_DIR)

# --- URL Simpact ---
API_DB_URL = "https://simpact.app/api/db"
API_AVATAR_URL = "https://simpact.app/api/assets/avatar/{char_name}.png"
API_WEAPON_URL = "https://simpact.app/api/assets/weapons/{weapon_name}.png"
API_ARTIFACT_URL = "https://simpact.app/api/assets/artifacts/{set}_flower.png"

# Ссылка на детали замера в gcsim
GCSIM_DB_URL = "https://gcsim.app/db/{record_id}"

# --- Параметры выгрузки ---
PAGE_SIZE = 100  # размер страницы при выгрузке из Simpact
REQUEST_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 30
PAGE_DELAY = 0.3  # задержка между запросами к API, сек

# --- Правила отбора записей ---
# Минимальная средняя длина замера (sim_duration.mean) в секундах.
# Записи со средней длиной <= этого значения отбраковываются.
MIN_SIM_DURATION = 47.0

# --- Ключи списков в objects.json ---
CHARACTER_LISTS = [
    "new_event_leg_names_list",
    "old_event_leg_names_list",
    "standart_leg_names_list",
    "epic_names_list",
]
WEAPON_LISTS = [
    "leg_weapons_list",
    "bp_or_event_weapons_list",
    "epic_weapons_list",
    "rare_weapons_list",
]
ALL_LISTS = CHARACTER_LISTS + WEAPON_LISTS


def ensure_cache_dirs() -> None:
    """Создаёт папки кэша, если их ещё нет."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for d in ASSET_DIRS:
        d.mkdir(parents=True, exist_ok=True)