"""Правила отбора записей и вычисление флагов наборов фильтров."""

from . import config, models


def _has_forbidden_weapon(team, om) -> bool:
    """Правило 1: запрещено оружие из списка leg_weapons_list."""
    for member in team:
        weapon = models.member_weapon_name(member)
        if weapon and om.classify_weapon(weapon) == "leg_weapons_list":
            return True
    return False


def _has_forbidden_cons(team, om) -> bool:
    """Правила 2-4: превышение cons у легендарных персонажей."""
    limits = {
        "new_event_leg_names_list": 0,
        "old_event_leg_names_list": 1,
        "standart_leg_names_list": 4,
    }
    for member in team:
        name = models.member_name(member)
        cls = om.classify_character(name)
        if cls in limits and models.member_cons(member) > limits[cls]:
            return True
    return False


def is_allowed(raw_record: dict, om) -> bool:
    """Проверяет, что запись проходит все правила отбора (1-8)."""
    team = (raw_record.get("summary", {}) or {}).get("team", []) or []

    # Правило 6: число персонажей не меньше 4
    if len(team) < 4:
        return False
    # Правило 5: уровень каждого персонажа равен 90
    if any(int(member.get("level", 0) or 0) != 90 for member in team):
        return False
    # Правило 7: у каждого персонажа должно быть поле sets
    if any(member.get("sets") is None for member in team):
        return False
    # Правило 1: запрещённое оружие
    if _has_forbidden_weapon(team, om):
        return False
    # Правила 2-4: превышение cons
    if _has_forbidden_cons(team, om):
        return False
    # Правило 8: средняя длина замера должна быть больше MIN_SIM_DURATION
    sim_duration = ((raw_record.get("summary") or {}).get("sim_duration") or {}).get("mean")
    if sim_duration is None or float(sim_duration) <= config.MIN_SIM_DURATION:
        return False
    return True


def compute_flags(team, om) -> dict:
    """
    Вычисляет флаги наборов фильтров для отряда.

    kqms: у всех персонажей из new/old/standart списков cons == 0.
    kqms_selector: у new cons == 0; у old/standart cons < 2.
    ftp: ограничения как у kqms, но число персонажей из epic_names_list > 2.
    """
    kqms = True
    kqms_selector = True
    for member in team:
        name = models.member_name(member)
        cls = om.classify_character(name)
        if cls not in ("new_event_leg_names_list", "old_event_leg_names_list", "standart_leg_names_list"):
            continue
        cons = models.member_cons(member)
        if cons != 0:
            kqms = False
        if cls == "new_event_leg_names_list":
            if cons != 0:
                kqms_selector = False
        else:  # old / standart
            if cons >= 2:
                kqms_selector = False

    # ftp: как kqms, но дополнительно более 2 персонажей из epic_names_list
    epic_count = sum(
        1
        for member in team
        if om.classify_character(models.member_name(member)) == "epic_names_list"
    )
    ftp = kqms and epic_count > 2

    return {"kqms": kqms, "kqms_selector": kqms_selector, "ftp": ftp}