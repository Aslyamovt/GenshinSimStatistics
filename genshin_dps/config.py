"""Конфигурация приложения Genshin Sim Statistics: пути, URL, константы."""

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

# --- Имя и версия сервиса ---
APP_NAME = "Genshin Sim Statistics"
APP_VERSION = "2.0.1"

# --- Пути к кэшу и файлам ---
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = CACHE_DIR / "local_db.json"
OBJECTS_PATH = CACHE_DIR / "objects.json"
# Резервная копия классификационных списков рядом с приложением/.exe. Если в
# кэше объектов ещё нет, этот файл копируется в cache/objects.json при первом
# запуске (поставляется вместе с .exe через build.py).
DEFAULT_OBJECTS_PATH = BASE_DIR / "objects.json"

# --- База замеров Wfpsim (хранится отдельно от базы Simpact) ---
WFPSIM_DB_PATH = CACHE_DIR / "wfpsim_db.json"
# Классификация неизвестных объектов, найденных в замерах Wfpsim.
# Структура файла такая же, как у objects.json; объекты из обоих файлов
# объединяются при фильтрации по персонажам во вкладке Wfpsim database.
WFPSIM_OBJECTS_PATH = CACHE_DIR / "wfpsim_objects.json"
DEFAULT_PNG = CACHE_DIR / "default.png"

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

# --- URL Wfpsim (неофициальный форк gcsim с базой замеров) ---
# Ссылка в формате, который пользователь вводит в окне добавления записи.
WFPSIM_SHARE_URL = "https://wfpsim.com/sh/{record_id}"
# API-ссылка, по которой запрашивается JSON замера.
WFPSIM_API_SHARE_URL = "https://wfpsim.com/api/share/{record_id}"

# --- Интерфейс вкладки Wfpsim database ---
WFPSIM_CARDS_PER_PAGE = 5  # количество карточек замеров на одной странице

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