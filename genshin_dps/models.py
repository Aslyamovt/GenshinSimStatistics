"""Модели данных и вспомогательные функции для работы с записями замеров."""


def member_cons(member: dict) -> int:
    """Значение cons персонажа; отсутствующее поле считается 0."""
    try:
        return int(member.get("cons", 0) or 0)
    except (TypeError, ValueError):
        return 0


def member_weapon_name(member: dict) -> str:
    """Название оружия персонажа (в нижнем регистре) или пустая строка."""
    weapon = member.get("weapon") or {}
    return (weapon.get("name") or "").lower()


def member_name(member: dict) -> str:
    """Имя персонажа в нижнем регистре."""
    return (member.get("name") or "").lower()


def canonical_names(team: list) -> list:
    """Канонический список имён отряда (отсортированный) для сопоставления составов."""
    return sorted(member_name(m) for m in team)


def team_to_record(raw_record: dict) -> dict:
    """Преобразует сырую запись из Simpact в компактную запись локальной базы."""
    summary = raw_record.get("summary", {})
    team = summary.get("team", []) or []
    return {
        "_id": raw_record.get("_id"),
        "mean_dps_per_target": summary.get("mean_dps_per_target", 0),
        "names": canonical_names(team),
        "team": team,
        "description": (raw_record.get("description") or ""),
    }