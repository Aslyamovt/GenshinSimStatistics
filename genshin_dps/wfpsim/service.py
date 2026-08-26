"""Сервис Wfpsim: запрос записей из API Wfpsim и получение изображений.

Изображения (аватары, оружие, наборы артефактов) Wfpsim не хранит собственное
хранилище, поэтому они запрашиваются из базы Simpact (через ``SimpactDownloader``).
Сначала проверяется локальный кэш, затем выполняется загрузка; если артефакт
отсутствует в базе Simpact, используется ``cache/default.png``.
"""

import re

import requests

from .. import config
from ..downloader import SimpactDownloader
from . import models


class NoResultsError(Exception):
    """Запись существует в базе Wfpsim, но не содержит результатов замеров урона."""


def _has_results(raw: dict) -> bool:
    """Проверяет, что в ответе Wfpsim есть результаты замеров урона."""
    statistics = raw.get("statistics") or {}
    dps = (statistics.get("dps") or {}).get("mean")
    return dps is not None and bool(raw.get("character_details"))


class WfpsimService:
    """Инкапсулирует HTTP-взаимодействие с API Wfpsim и загрузку ассетов."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "genshin-sim-statistics/2.0"}
        )
        self.dl = SimpactDownloader()

    # --- Работа со ссылками ---

    @staticmethod
    def extract_id(url: str):
        """Извлекает ID записи из ссылки вида .../sh/{ID} или .../api/share/{ID}."""
        if not url:
            return None
        match = re.search(r"/(?:sh|api/share)/([A-Za-z0-9_-]+)", url.strip())
        return match.group(1) if match else None

    # --- Запрос записей ---

    def fetch_share(self, record_id: str) -> dict:
        """Возвращает сырой JSON записи по её ID из базы Wfpsim."""
        url = config.WFPSIM_API_SHARE_URL.format(record_id=record_id)
        resp = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def fetch_and_build(self, record_id: str, wfpsim_url: str = None) -> dict:
        """Получает запись из Wfpsim и преобразует её в формат локальной базы.

        ``wfpsim_url`` — исходная ссылка, введённая пользователем; она сохраняется
        в записи как есть (для «Подробнее на wfpsim» и замены ссылки).

        Если в базе Wfpsim для записи нет результатов замеров урона, бросается
        ``NoResultsError``.
        """
        raw = self.fetch_share(record_id)
        if not _has_results(raw):
            raise NoResultsError(record_id)
        return models.to_record(raw, record_id, wfpsim_url=wfpsim_url)

    # --- Загрузка ассетов (через базу Simpact с fallback на default.png) ---

    def _asset(self, path):
        """Возвращает путь к файлу или путь к default.png при отсутствии."""
        return path if path else config.DEFAULT_PNG

    def avatar_path(self, member: dict):
        name = ((member.get("name") or "").lower()).strip()
        return self._asset(self.dl.download_avatar(name) if name else None)

    def weapon_path(self, member: dict):
        weapon = ((member.get("weapon") or {}).get("name") or "").lower().strip()
        return self._asset(self.dl.download_weapon(weapon) if weapon else None)

    def artifact_paths(self, member: dict):
        """Возвращает список путей к иконкам наборов артефактов персонажа."""
        result = []
        for set_name in (member.get("sets") or {}).keys():
            set_name = (set_name or "").lower().strip()
            if not set_name:
                continue
            result.append(self._asset(self.dl.download_artifact(set_name)))
        return result