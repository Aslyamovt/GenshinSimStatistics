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

    def _download(self, folder, fname: str, url: str, force: bool = False):
        """Скачивает файл, если его ещё нет (или при force=True). Возвращает путь."""
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / fname
        if path.exists() and not force:
            return path
        try:
            resp = self.session.get(url, timeout=config.DOWNLOAD_TIMEOUT)
            resp.raise_for_status()
            path.write_bytes(resp.content)
        except Exception:
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
    """Скачивает и возвращает пути к ассетам персонажа."""
    name = (member.get("name") or "").lower()
    avatar = downloader.download_avatar(name, force)

    weapon = (member.get("weapon") or {}).get("name", "")
    weapon_path = downloader.download_weapon(weapon, force) if weapon else None

    artifact_paths = []
    for set_name in (member.get("sets") or {}).keys():
        artifact_paths.append(downloader.download_artifact(set_name, force))

    return {"avatar": avatar, "weapon": weapon_path, "artifacts": artifact_paths}


def download_record_assets(downloader: SimpactDownloader, record: dict, force: bool = False) -> None:
    """Скачивает ассеты для всех персонажей отряда."""
    for member in record.get("team", []):
        member_assets(downloader, member, force)