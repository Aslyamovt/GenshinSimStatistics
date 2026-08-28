"""Преобразование записей Wfpsim в формат базы Simpact для вкладки DPS Leaders.

Трансформированные записи отбираются и приводятся к формату записей базы Simpact
по тем же правилам, что и записи Simpact (``genshin_dps/filters.py``), и хранятся
в отдельном файле ``cache/wfpsim_records.json`` — не смешиваясь ни с локальной
базой Simpact (``cache/local_db.json``), ни с исходной базой Wfpsim
(``cache/wfpsim_db.json``). Обрабатываются только записи с флагом
``not_valid = False``.
"""

import json
from pathlib import Path

from .. import config, filters, models

# Режимы фильтра «Источник» во вкладке Genshin DPS Leaders.
MODE_GCSIM = "gcsim"
MODE_WF_UNIQUE = "wf_unique"
MODE_WF_ALL = "wf_all"

# Значение поля ``source`` для записей, полученных из базы Wfpsim.
SOURCE_WFPSIM = "wfpsim"


def _comp_key(record):
    """Ключ состава: отсортированный набор пар (имя, cons)."""
    comp = record.get("composition")
    if comp:
        return tuple((str(n), int(c or 0)) for n, c in comp)
    return tuple(
        sorted(
            (m.get("name", ""), int(m.get("cons", 0) or 0))
            for m in (record.get("team", []) or [])
        )
    )


def transform_record(rec, om):
    """Преобразует запись Wfpsim в формат базы Simpact или возвращает ``None``.

    Применяются правила отбора, аналогичные записям базы Simpact: состав не
    менее 4 персонажей, уровень 90, наличие наборов артефактов, отсутствие
    запрещённого оружия и превышений cons. Правило длительности замера
    (gcsim-specific) к записям Wfpsim не применяется, т.к. у них нет поля
    ``sim_duration``.
    """
    if rec.get("not_valid"):
        return None
    team = rec.get("team", []) or []
    if len(team) < 4:
        return None
    if any(int(m.get("level", 0) or 0) != 90 for m in team):
        return None
    if any(m.get("sets") is None for m in team):
        return None
    if filters._has_forbidden_weapon(team, om):
        return None
    if filters._has_forbidden_cons(team, om):
        return None

    return {
        "_id": rec.get("_id"),
        "mean_dps_per_target": rec.get("mean_dps_per_target", 0),
        "names": sorted(str(m.get("name", "")).lower() for m in team),
        "composition": models.canonical_composition(team),
        "team": team,
        "description": rec.get("description", ""),
        "flags": filters.compute_flags(team, om),
        "source": SOURCE_WFPSIM,
        "wfpsim_url": rec.get("wfpsim_url"),
        "created_at": rec.get("created_at"),
    }


def transform_records(records, om):
    """Преобразует список записей Wfpsim, отбрасывая непригодные."""
    return [r for r in (transform_record(rec, om) for rec in (records or [])) if r]


def union_objects_manager(base_om):
    """Возвращает менеджер объектов, объединяющий objects.json и wfpsim_objects.json."""
    from ..objects_manager import ObjectsManager, UnionObjectsManager

    extra = ObjectsManager(config.WFPSIM_OBJECTS_PATH, seed_from_default=False)
    return UnionObjectsManager(base_om, extra)


class WfpsimRecords:
    """Хранит трансформированные записи Wfpsim в отдельном файле."""

    def __init__(self, path=None):
        self.path = Path(path) if path else config.WFPSIM_RECORDS_PATH
        self.records = []
        self.load()

    def load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self.records = data if isinstance(data, list) else []
        except Exception:
            self.records = []

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def rebuild(self, om):
        """Пересобирает трансформированные записи из текущей базы Wfpsim."""
        from .db import WfpsimDB

        self.records = transform_records(WfpsimDB().records, om)
        self.save()


def _dedupe_by_comp(records):
    """Оставляет по одной записи на состав (с максимальным уроном)."""
    best = {}
    for r in records or []:
        k = _comp_key(r)
        cur = best.get(k)
        if cur is None or r.get("mean_dps_per_target", 0) > cur.get(
            "mean_dps_per_target", 0
        ):
            best[k] = r
    return best


def _sort_by_dps(records):
    """Сортирует записи по убыванию урона."""
    return sorted(
        records, key=lambda r: r.get("mean_dps_per_target", 0), reverse=True
    )


def merge_sources(ldb_records, wf_records, mode):
    """Объединяет записи Simpact (LEFT) и Wfpsim (RIGHT) по выбранному источнику.

      - ``MODE_GCSIM`` — только записи Simpact (LEFT).
      - ``MODE_WF_UNIQUE`` — LEFT ONLY + RIGHT ONLY: для пересечения LEFT∩RIGHT
        показывается вариант из LEFT с наибольшим уроном.
      - ``MODE_WF_ALL`` — LEFT ONLY + RIGHT ONLY + для пересечения LEFT∩RIGHT
        выбирается запись (LEFT или RIGHT) с наибольшим уроном.

    Итоговый список всегда отсортирован по убыванию урона (общая сортировка
    для записей Simpact и Wfpsim).
    """
    left = _dedupe_by_comp(ldb_records)
    right = _dedupe_by_comp(wf_records)

    if mode == MODE_GCSIM:
        return _sort_by_dps(list(left.values()))

    left_comps = set(left)
    right_only = {k: r for k, r in right.items() if k not in left_comps}

    merged = dict(left)
    merged.update(right_only)
    if mode == MODE_WF_ALL:
        # Для пересечения выбираем запись с большим уроном.
        for k, r in right.items():
            if k in left_comps and r.get("mean_dps_per_target", 0) > left[k].get(
                "mean_dps_per_target", 0
            ):
                merged[k] = r

    return _sort_by_dps(list(merged.values()))