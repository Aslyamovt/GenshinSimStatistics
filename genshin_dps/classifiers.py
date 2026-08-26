"""Сбор и классификация неизвестных персонажей и оружия."""

from . import config
from . import models


class UnknownCollector:
    """Собирает уникальные неизвестные имена персонажей и оружия из записей."""

    def __init__(self, om):
        self.om = om
        self.unknown_chars = set()
        self.unknown_weapons = set()

    def scan_record(self, raw_record: dict) -> None:
        team = (raw_record.get("summary", {}) or {}).get("team", []) or []
        for member in team:
            name = models.member_name(member)
            if name and self.om.classify_character(name) is None:
                self.unknown_chars.add(name)
            weapon = models.member_weapon_name(member)
            if weapon and self.om.classify_weapon(weapon) is None:
                self.unknown_weapons.add(weapon)

    def scan_records(self, raw_records) -> None:
        for rec in raw_records:
            self.scan_record(rec)

    def is_empty(self) -> bool:
        return not self.unknown_chars and not self.unknown_weapons

    def items(self):
        """Возвращает список (тип, имя), где тип 'char' или 'weapon'."""
        result = [("char", n) for n in sorted(self.unknown_chars)]
        result += [("weapon", n) for n in sorted(self.unknown_weapons)]
        return result


def choices_for(kind: str) -> list:
    """Допустимые списки для классификации по типу объекта."""
    return config.CHARACTER_LISTS if kind == "char" else config.WEAPON_LISTS


def recommended_list(kind: str) -> str:
    """Рекомендуемый список по умолчанию."""
    if kind == "char":
        return "epic_names_list"
    return "rare_weapons_list"


def apply_classifications(om, char_map: dict, weapon_map: dict) -> None:
    """Применяет результаты классификации пользователя к objects.json."""
    for name, list_key in (char_map or {}).items():
        if list_key:
            om.add_character(name, list_key)
    for name, list_key in (weapon_map or {}).items():
        if list_key:
            om.add_weapon(name, list_key)