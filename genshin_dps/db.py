"""Локальная база отрядов (cache/local_db.json) и логика merge."""

import json
from pathlib import Path

from . import config, models


class LocalDB:
    """Хранит записи об отрядах, уникальные по составу (набор имён + cons)."""

    def __init__(self, path=None):
        self.path = Path(path) if path else config.DB_PATH
        self.records = []
        self._by_composition = {}
        self.load()

    def load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.records = json.load(f)
        else:
            self.records = []
        self.reindex()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def _composition_key(self, record: dict) -> tuple:
        """
        Ключ состава записи: отсортированный набор пар (имя, cons).

        Записи с одинаковыми именами, но разными значениями cons считаются разными.
        Для старых записей без поля ``composition`` ключ вычисляется из команды.
        """
        comp = record.get("composition")
        if comp:
            return tuple((n, int(c or 0)) for n, c in comp)
        team = record.get("team", []) or []
        return tuple(
            (models.member_name(m), models.member_cons(m)) for m in team
        )

    def reindex(self):
        self._by_composition = {}
        for rec in self.records:
            self._by_composition.setdefault(self._composition_key(rec), []).append(rec)

    def merge(self, record: dict):
        """Добавляет/обновляет запись в базе по правилам дедупликации."""
        record.setdefault(
            "flags", {"kqms": False, "kqms_selector": False, "ftp": False}
        )
        record.setdefault("names", sorted(m.get("name", "") for m in record.get("team", [])))
        if "composition" not in record:
            record["composition"] = models.canonical_composition(record.get("team", []))

        # 1. Обновление по идентичному id
        for i, existing in enumerate(self.records):
            if existing.get("_id") == record.get("_id"):
                self.records[i] = record
                self.reindex()
                return

        # 2. Дедупликация по составу (имя + cons): заменяем только при большем уроне
        comp = self._composition_key(record)
        existing_list = self._by_composition.get(comp, [])
        for existing in existing_list:
            if record.get("mean_dps_per_target", 0) > existing.get("mean_dps_per_target", 0):
                idx = self.records.index(existing)
                self.records[idx] = record
            self.reindex()
            return

        # 3. Новый состав
        self.records.append(record)
        self.reindex()

    def sorted_records(self):
        """Все записи, отсортированные по убыванию урона."""
        return sorted(self.records, key=lambda r: r.get("mean_dps_per_target", 0), reverse=True)