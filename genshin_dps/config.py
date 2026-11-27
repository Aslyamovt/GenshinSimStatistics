"""Конфигурация приложения Genshin Sim Statistics: пути, URL, константы.

Любое значение из этого модуля можно переопределить во внешнем файле
``config.json``, который располагается рядом с исполняемым файлом (при запуске
собранного ``.exe``) или в корне проекта (при запуске из исходников). Формат —
плоский JSON-объект, ключи которого совпадают с именами переменных модуля::

    {
      "APP_NAME": "Genshin Sim Statistics",
      "PAGE_SIZE": 200,
      "CACHE_DIR": "data",
      "DB_PATH": "local_db.json"
    }

Правила разбора:

* пути разрешаются относительно ``BASE_DIR`` (папка с ``.exe`` или корень
  проекта);
* если значение пути не содержит разделителей каталогов (например,
  ``"local_db.json"``), оно трактуется как имя файла внутри каталога по
  умолчанию (``CACHE_DIR`` для файлов кэша, ``BASE_DIR`` — для
  ``DEFAULT_OBJECTS_PATH``);
* абсолютные пути используются как есть;
* отсутствующий ключ оставляет значение по умолчанию.

Значения ``ASSET_DIRS`` и ``ALL_LISTS`` являются производными и при отсутствии
в JSON пересчитываются из соответствующих переменных.
"""

import json
import sys
from pathlib import Path

# Имя внешнего файла конфигурации (рядом с .exe / в корне проекта).
CONFIG_FILENAME = "config.json"


def _base_dir() -> Path:
    """Корневая директория приложения.

    При запуске из исходников это папка, содержащая пакет ``genshin_dps``.
    При запуске собранного .exe — директория, в которой лежит исполняемый файл
    (туда кладутся ``objects.json``, ``config.json``, кэш и прочие данные).
    """
    if getattr(sys, "frozen", False):  # PyInstaller onefile
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# Корень проекта (папка, содержащая пакет genshin_dps или сам .exe).
# Не настраивается через config.json — вычисляется автоматически.
BASE_DIR = _base_dir()


# ---------------------------------------------------------------------------
# Значения по умолчанию
# ---------------------------------------------------------------------------

# --- Имя и версия сервиса ---
APP_NAME = "Genshin Sim Statistics"
APP_VERSION = "4.1.0"

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
# Трансформированные записи Wfpsim для отображения во вкладке Genshin DPS Leaders.
# Отдельный файл: не смешивается ни с local_db.json (Simpact), ни с wfpsim_db.json.
WFPSIM_RECORDS_PATH = CACHE_DIR / "wfpsim_records.json"

# --- База Custom gcsim records (отдельная от Simpact и Unofficial) ---
# Сырые записи пользовательских замеров gcsim (формат как у wfpsim_db.json).
CUSTOM_GCSIM_DB_PATH = CACHE_DIR / "custom_gcsim_db.json"
# Трансформированные записи для вкладки Genshin DPS Leaders.
CUSTOM_GCSIM_RECORDS_PATH = CACHE_DIR / "custom_gcsim_records.json"

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

# --- URL gcsim для вкладки Custom gcsim records ---
# Ссылка в формате, который пользователь вводит в окне добавления записи.
GCSIM_SHARE_URL = "https://gcsim.app/sh/{record_id}"
# API-ссылка, по которой запрашивается JSON замера.
GCSIM_API_SHARE_URL = "https://gcsim.app/api/share/{record_id}"

# --- URL Wfpsim (неофициальный форк gcsim с базой замеров) ---
# Ссылка в формате, который пользователь вводит в окне добавления записи.
WFPSIM_SHARE_URL = "https://wfpsim.com/sh/{record_id}"
# API-ссылка, по которой запрашивается JSON замера.
WFPSIM_API_SHARE_URL = "https://wfpsim.com/api/share/{record_id}"

# --- URL sim.kqm.gg (альтернативный источник записей Unofficial database) ---
# Ссылка в формате, который пользователь вводит в окне добавления записи.
KQM_SHARE_URL = "https://sim.kqm.gg/sh/{record_id}"
# API-ссылка, по которой запрашивается JSON замера.
KQM_API_SHARE_URL = "https://sim.kqm.gg/api/share/{record_id}"

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


# ---------------------------------------------------------------------------
# Загрузка внешнего config.json
# ---------------------------------------------------------------------------


def _config_path() -> Path:
    """Путь к внешнему файлу конфигурации."""
    return BASE_DIR / CONFIG_FILENAME


def _read_config() -> dict:
    """Читает внешний config.json; при ошибке возвращает пустой словарь."""
    path = _config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[config] Не удалось прочитать {path}: {exc}")
        return {}
    if not isinstance(data, dict):
        print(f"[config] Файл {path} должен содержать JSON-объект")
        return {}
    return data


def _as_str(value, default):
    if value is None:
        return default
    return str(value)


def _as_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_list(value, default):
    if value is None:
        return default
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return default


def _as_path(value, default, parent: Path) -> Path:
    """Преобразует значение из JSON в путь.

    * абсолютный путь используется как есть;
    * имя без каталогов (``"file.json"``) кладётся в ``parent``;
    * путь с каталогами разрешается относительно ``BASE_DIR``.
    """
    if value is None:
        return default
    try:
        path = Path(str(value)).expanduser()
    except (TypeError, ValueError):
        return default
    if path.is_absolute():
        return path
    if path.parent == Path("."):
        return parent / path
    return BASE_DIR / path


def _apply_user_config() -> None:
    """Переопределяет значения модуля данными из внешнего config.json."""
    global APP_NAME, APP_VERSION
    global CACHE_DIR, DB_PATH, OBJECTS_PATH, DEFAULT_OBJECTS_PATH
    global WFPSIM_DB_PATH, WFPSIM_OBJECTS_PATH, WFPSIM_RECORDS_PATH
    global CUSTOM_GCSIM_DB_PATH, CUSTOM_GCSIM_RECORDS_PATH
    global DEFAULT_PNG, AVATARS_DIR, WEAPONS_DIR, ARTIFACTS_DIR, ASSET_DIRS
    global API_DB_URL, API_AVATAR_URL, API_WEAPON_URL, API_ARTIFACT_URL
    global GCSIM_DB_URL, GCSIM_SHARE_URL, GCSIM_API_SHARE_URL
    global WFPSIM_SHARE_URL, WFPSIM_API_SHARE_URL
    global KQM_SHARE_URL, KQM_API_SHARE_URL
    global PAGE_SIZE, REQUEST_TIMEOUT, DOWNLOAD_TIMEOUT, PAGE_DELAY
    global MIN_SIM_DURATION
    global CHARACTER_LISTS, WEAPON_LISTS, ALL_LISTS

    cfg = _read_config()
    if not cfg:
        return

    # --- Имя и версия ---
    APP_NAME = _as_str(cfg.get("APP_NAME"), APP_NAME)
    APP_VERSION = _as_str(cfg.get("APP_VERSION"), APP_VERSION)

    # --- Пути ---
    CACHE_DIR = _as_path(cfg.get("CACHE_DIR"), CACHE_DIR, BASE_DIR)
    DB_PATH = _as_path(cfg.get("DB_PATH"), CACHE_DIR / "local_db.json", CACHE_DIR)
    OBJECTS_PATH = _as_path(
        cfg.get("OBJECTS_PATH"), CACHE_DIR / "objects.json", CACHE_DIR
    )
    DEFAULT_OBJECTS_PATH = _as_path(
        cfg.get("DEFAULT_OBJECTS_PATH"), BASE_DIR / "objects.json", BASE_DIR
    )
    WFPSIM_DB_PATH = _as_path(
        cfg.get("WFPSIM_DB_PATH"), CACHE_DIR / "wfpsim_db.json", CACHE_DIR
    )
    WFPSIM_OBJECTS_PATH = _as_path(
        cfg.get("WFPSIM_OBJECTS_PATH"), CACHE_DIR / "wfpsim_objects.json", CACHE_DIR
    )
    WFPSIM_RECORDS_PATH = _as_path(
        cfg.get("WFPSIM_RECORDS_PATH"), CACHE_DIR / "wfpsim_records.json", CACHE_DIR
    )
    CUSTOM_GCSIM_DB_PATH = _as_path(
        cfg.get("CUSTOM_GCSIM_DB_PATH"),
        CACHE_DIR / "custom_gcsim_db.json",
        CACHE_DIR,
    )
    CUSTOM_GCSIM_RECORDS_PATH = _as_path(
        cfg.get("CUSTOM_GCSIM_RECORDS_PATH"),
        CACHE_DIR / "custom_gcsim_records.json",
        CACHE_DIR,
    )
    DEFAULT_PNG = _as_path(
        cfg.get("DEFAULT_PNG"), CACHE_DIR / "default.png", CACHE_DIR
    )
    AVATARS_DIR = _as_path(
        cfg.get("AVATARS_DIR"), CACHE_DIR / "avatars", CACHE_DIR
    )
    WEAPONS_DIR = _as_path(
        cfg.get("WEAPONS_DIR"), CACHE_DIR / "weapons", CACHE_DIR
    )
    ARTIFACTS_DIR = _as_path(
        cfg.get("ARTIFACTS_DIR"), CACHE_DIR / "artifacts", CACHE_DIR
    )

    if "ASSET_DIRS" in cfg:
        dirs = _as_list(cfg.get("ASSET_DIRS"), [])
        if dirs:
            ASSET_DIRS = tuple(_as_path(d, CACHE_DIR / d, CACHE_DIR) for d in dirs)
    else:
        ASSET_DIRS = (AVATARS_DIR, WEAPONS_DIR, ARTIFACTS_DIR)

    # --- URL ---
    API_DB_URL = _as_str(cfg.get("API_DB_URL"), API_DB_URL)
    API_AVATAR_URL = _as_str(cfg.get("API_AVATAR_URL"), API_AVATAR_URL)
    API_WEAPON_URL = _as_str(cfg.get("API_WEAPON_URL"), API_WEAPON_URL)
    API_ARTIFACT_URL = _as_str(cfg.get("API_ARTIFACT_URL"), API_ARTIFACT_URL)
    GCSIM_DB_URL = _as_str(cfg.get("GCSIM_DB_URL"), GCSIM_DB_URL)
    GCSIM_SHARE_URL = _as_str(cfg.get("GCSIM_SHARE_URL"), GCSIM_SHARE_URL)
    GCSIM_API_SHARE_URL = _as_str(
        cfg.get("GCSIM_API_SHARE_URL"), GCSIM_API_SHARE_URL
    )
    WFPSIM_SHARE_URL = _as_str(cfg.get("WFPSIM_SHARE_URL"), WFPSIM_SHARE_URL)
    WFPSIM_API_SHARE_URL = _as_str(
        cfg.get("WFPSIM_API_SHARE_URL"), WFPSIM_API_SHARE_URL
    )
    KQM_SHARE_URL = _as_str(cfg.get("KQM_SHARE_URL"), KQM_SHARE_URL)
    KQM_API_SHARE_URL = _as_str(
        cfg.get("KQM_API_SHARE_URL"), KQM_API_SHARE_URL
    )

    # --- Параметры выгрузки и правила отбора ---
    PAGE_SIZE = _as_int(cfg.get("PAGE_SIZE"), PAGE_SIZE)
    REQUEST_TIMEOUT = _as_int(cfg.get("REQUEST_TIMEOUT"), REQUEST_TIMEOUT)
    DOWNLOAD_TIMEOUT = _as_int(cfg.get("DOWNLOAD_TIMEOUT"), DOWNLOAD_TIMEOUT)
    PAGE_DELAY = _as_float(cfg.get("PAGE_DELAY"), PAGE_DELAY)
    MIN_SIM_DURATION = _as_float(cfg.get("MIN_SIM_DURATION"), MIN_SIM_DURATION)

    # --- Списки классификации ---
    CHARACTER_LISTS = _as_list(cfg.get("CHARACTER_LISTS"), CHARACTER_LISTS)
    WEAPON_LISTS = _as_list(cfg.get("WEAPON_LISTS"), WEAPON_LISTS)
    if "ALL_LISTS" in cfg:
        ALL_LISTS = _as_list(cfg.get("ALL_LISTS"), ALL_LISTS)
    else:
        ALL_LISTS = CHARACTER_LISTS + WEAPON_LISTS


def ensure_cache_dirs() -> None:
    """Создаёт папки кэша, если их ещё нет."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for d in ASSET_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# Применяем пользовательские настройки при импорте модуля.
_apply_user_config()
