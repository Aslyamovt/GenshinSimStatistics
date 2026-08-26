"""Локальная база замеров Wfpsim.

База хранится в отдельном файле (``cache/wfpsim_db.json``) и никак не смешивается
с базой Simpact (``cache/local_db.json``). Каждая запись уникальна по полю ``_id``
(идентификатор записи в базе Wfpsim).
"""

import json
from pathlib import Path

from .. import config


class WfpsimDB:
    """Хранит записи замеров урона из Wfpsim, уникальные по ``_id``."""

    def __init__(self, path=None):
        self.path = Path(path) if path else config.WFPSIM_DB_PATH
        self.records = []
        self.load()

    def load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.records = json.load(f)
        else:
            self.records = []
        if not isinstance(self.records, list):
            self.records = []

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def get(self, record_id: str):
        for rec in self.records:
            if rec.get("_id") == record_id:
                return rec
        return None

    def add_or_update(self, record: dict):
        """Добавляет новую запись или обновляет существующую по ``_id``."""
        record.setdefault("not_valid", False)
        for i, existing in enumerate(self.records):
            if existing.get("_id") == record.get("_id"):
                self.records[i] = record
                self.save()
                return record
        self.records.append(record)
        self.save()
        return record

    def delete(self, record_id: str) -> bool:
        before = len(self.records)
        self.records = [r for r in self.records if r.get("_id") != record_id]
        changed = len(self.records) != before
        if changed:
            self.save()
        return changed

    def mark_not_valid(self, record_id: str) -> bool:
        for rec in self.records:
            if rec.get("_id") == record_id:
                rec["not_valid"] = True
                self.save()
                return True
        return False