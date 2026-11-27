"""Выгрузка данных из Simpact и скачивание ассетов (аватары, оружие, артефакты)."""

import json
import time
from urllib.parse import quote

import requests

from . import config


class SimpactDownloader:
    """Инкапсулирует HTTP-взаимодействие с API Simpact."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "genshin-dps-leaders/1.0"})
        self._default_image = None
        self._default_checked = False

    # --- Выгрузка записей базы замеров ---

    def _db_url(self, skip: int) -> str:
        query = {
            "query": {},
            "limit": config.PAGE_SIZE,
            "skip": skip,
            "sort": {"summary.mean_dps_per_target": -1},
        }
        return config.API_DB_URL + "?q=" + quote(json.dumps(query))

    def fetch_page(self, skip: int):
        """Возвращает список записей для страницы с указанным skip."""
        url = self._db_url(skip)
        resp = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("data", []) or []

    def fetch_all(self, on_page=None) -> int:
        """
        Итеративно выгружает все записи из базы Simpact.
        SKIP увеличивается на PAGE_SIZE, пока в ответе не придёт меньше 100 записей.
        on_page(data, skip) вызывается после каждой страницы.
        Возвращает общее число выгруженных записей.
        """
        skip = 0
        total = 0
        while True:
            data = self.fetch_page(skip)
            total += len(data)
            if on_page:
                on_page(data, skip)
            if len(data) < config.PAGE_SIZE:
                break
            skip += config.PAGE_SIZE
            time.sleep(config.PAGE_DELAY)
        return total

    # --- Скачивание ассетов ---

    def _default_image_bytes(self):
        """Байты ``default.png`` (или None, если файла нет).

        API Simpact для отсутствующих иконок возвращает HTTP 200 с содержимым
        ``default.png``. Чтобы не плодить копии этого изображения под именами
        недостающих ресурсов, сравниваем загруженные данные с локальным
        ``default.png``.
        """
        if not self._default_checked:
            self._default_checked = True
            try:
                self._default_image = config.DEFAULT_PNG.read_bytes()
            except OSError:
                self._default_image = None
        return self._default_image

    def _download(self, folder, fname: str, url: str, force: bool = False):
        """Скачивает файл, если его ещё нет (или при force=True). Возвращает путь.

        Если API вернул ``default.png`` (иконка отсутствует), файл не создаётся,
        а возвращается ``None`` — вызывающая сторона подставит ``default.png``
        для отображения.
        """
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / fname
        default_data = self._default_image_bytes()

        if path.exists() and not force:
            # Копии default.png, созданные прежними версиями, считаем
            # отсутствующими и удаляем, чтобы кэш не засорялся.
            if default_data is not None:
                try:
                    if path.read_bytes() == default_data:
                        path.unlink()
                        return None
                except OSError:
                    pass
            return path

        try:
            resp = self.session.get(url, timeout=config.DOWNLOAD_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return None

        content = resp.content
        if default_data is not None and content == default_data:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
            return None

        try:
            path.write_bytes(content)
        except OSError:
            return None
        return path

    def download_avatar(self, char_name: str, force: bool = False):
        url = config.API_AVATAR_URL.format(char_name=char_name.lower())
        return self._download(config.AVATARS_DIR, f"{char_name.lower()}.png", url, force)

    def download_weapon(self, weapon_name: str, force: bool = False):
        url = config.API_WEAPON_URL.format(weapon_name=weapon_name.lower())
        return self._download(config.WEAPONS_DIR, f"{weapon_name.lower()}.png", url, force)

    def download_artifact(self, set_name: str, force: bool = False):
        fname = f"{set_name.lower()}_flower.png"
        url = config.API_ARTIFACT_URL.format(set=set_name.lower())
        return self._download(config.ARTIFACTS_DIR, fname, url, force)


def member_assets(downloader: SimpactDownloader, member: dict, force: bool = False) -> dict:
    """Скачивает и возвращает пути к ассетам персонажа.

    Для отсутствующих изображений возвращается путь к ``default.png``, чтобы
    интерфейс показывал заглушку без создания копий под именами ресурсов.
    """
    name = (member.get("name") or "").lower()
    avatar = downloader.download_avatar(name, force) or config.DEFAULT_PNG

    weapon = (member.get("weapon") or {}).get("name", "")
    weapon_path = downloader.download_weapon(weapon, force) if weapon else None
    weapon_path = weapon_path or config.DEFAULT_PNG

    artifact_paths = []
    for set_name in (member.get("sets") or {}).keys():
        artifact_paths.append(
            downloader.download_artifact(set_name, force) or config.DEFAULT_PNG
        )

    return {"avatar": avatar, "weapon": weapon_path, "artifacts": artifact_paths}


def download_record_assets(downloader: SimpactDownloader, record: dict, force: bool = False) -> None:
    """Скачивает ассеты для всех персонажей отряда."""
    for member in record.get("team", []):
        member_assets(downloader, member, force)