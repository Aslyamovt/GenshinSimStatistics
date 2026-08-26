"""Локальная база отрядов (cache/local_db.json) и логика merge."""

import json
from pathlib import Path

from . import config


class LocalDB:
    """Хранит записи об отрядах, уникальные по составу (списку имён)."""

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

    def reindex(self):
        self._by_composition = {}
        for rec in self.records:
            self._by_composition.setdefault(tuple(rec.get("names", [])), []).append(rec)

    def merge(self, record: dict):
        """Добавляет/обновляет запись в базе по правилам дедупликации."""
        record.setdefault("flags", {"kqms": False, "kqms_selector": False})
        record.setdefault("names", sorted(m.get("name", "") for m in record.get("team", [])))

        # 1. Обновление по идентичному id
        for i, existing in enumerate(self.records):
            if existing.get("_id") == record.get("_id"):
                self.records[i] = record
                self.reindex()
                return

        comp = tuple(record.get("names", []))
        # 2. Дедупликация по составу: заменяем только при большем уроне
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