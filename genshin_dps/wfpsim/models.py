"""Преобразование данных Wfpsim в формат записей локальной базы.

Сырой JSON, получаемый от https://wfpsim.com/api/share/{ID}, приводится к формату,
аналогичному записям базы Simpact (см. ``genshin_dps/models.py``), чтобы карточка
замера могла отображаться так же, как карточки отрядов Genshin DPS Leaders.
Дополнительно сохраняются поля, специфичные для Wfpsim (config, ссылка и т.п.).
"""

import datetime
import re

from .. import config
from .. import models as sim_models


def _parse_cons_from_config(config_text: str, name: str) -> int:
    """Извлекает значение cons персонажа из текста конфига Wfpsim.

    Строка имеет вид: ``<name> char ... cons=N ...;``. Если поле не найдено,
    возвращается 0.
    """
    pattern = re.compile(
        r"\b" + re.escape(name) + r"\s+char\s+[^;]*?\bcons\s*=\s*(\d+)",
        re.IGNORECASE,
    )
    match = pattern.search(config_text or "")
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0


def _team_from_details(character_details: list, config_text: str) -> list:
    """Строит список персонажей ``team`` в формате базы Simpact."""
    team = []
    for cd in character_details or []:
        name = ((cd.get("name") or "").lower()).strip()
        if not name:
            continue
        weapon = cd.get("weapon") or {}
        sets = cd.get("sets") or {}

        # Поле cons присутствует в character_details не у всех персонажей —
        # при отсутствии берём значение из конфига.
        cons = cd.get("cons")
        if cons is None:
            cons = _parse_cons_from_config(config_text, name)

        member = {
            "name": name,
            "cons": int(cons or 0),
            "level": int(cd.get("level", 0) or 0),
            "weapon": {
                "name": ((weapon.get("name") or "").lower()).strip(),
                "refine": int(weapon.get("refine", 0) or 0),
            },
            "sets": {
                str(k).lower().strip(): int(v)
                for k, v in (sets or {}).items()
                if k
            },
        }
        team.append(member)
    return team


def to_record(raw: dict, record_id: str, wfpsim_url: str = None) -> dict:
    """Преобразует сырой JSON Wfpsim в запись локальной базы Wfpsim.

    Поля ``names``, ``composition`` и ``team`` совместимы с базой Simpact,
    поэтому карточки строятся теми же функциями. Поле ``config`` сохраняется
    отдельно и доступно для копирования.

    ``wfpsim_url`` — исходная ссылка, которую ввёл пользователь (например,
    ``https://wfpsim.com/sh/{ID}``). Если не передана, используется стандартный
    формат ``WFPSIM_SHARE_URL``.
    """
    statistics = raw.get("statistics") or {}
    dps = (statistics.get("dps") or {}).get("mean", 0)
    config_text = raw.get("config_file") or ""
    details = raw.get("character_details") or []
    team = _team_from_details(details, config_text)

    if not wfpsim_url:
        wfpsim_url = config.WFPSIM_SHARE_URL.format(record_id=record_id)

    return {
        "_id": record_id,
        "mean_dps_per_target": dps,
        "names": sim_models.canonical_names(team),
        "composition": sim_models.canonical_composition(team),
        "team": team,
        "config": config_text,
        "description": (raw.get("description") or ""),
        "not_valid": False,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "sim_version": (raw.get("sim_version") or ""),
        # Исходная пользовательская ссылка на запись Wfpsim
        "wfpsim_url": wfpsim_url,
    }