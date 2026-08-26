"""Работа с objects.json: загрузка, сохранение и классификация объектов."""

import json

from . import config


class ObjectsManager:
    """Управляет классификационными списками персонажей и оружия в objects.json."""

    def __init__(self, path=None):
        self.path = path or config.OBJECTS_PATH
        self.data = self.load()

    def load(self):
        """Загружает objects.json; при отсутствии создаёт пустую структуру."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        # Гарантируем наличие всех ключей
        for key in config.ALL_LISTS:
            data.setdefault(key, [])
        return data

    def save(self, data=None):
        """Сохраняет данные обратно в objects.json."""
        data = data if data is not None else self.data
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get(self, key):
        """Возвращает список по ключу."""
        return self.data.get(key, [])

    def classify_character(self, name):
        """Возвращает ключ списка, к которому относится персонаж, или None."""
        name = (name or "").lower()
        for key in config.CHARACTER_LISTS:
            if name in self.data.get(key, []):
                return key
        return None

    def classify_weapon(self, name):
        """Возвращает ключ списка, к которому относится оружие, или None."""
        name = (name or "").lower()
        for key in config.WEAPON_LISTS:
            if name in self.data.get(key, []):
                return key
        return None

    def add_character(self, name, list_key):
        """Добавляет персонажа в указанный список и сохраняет changes."""
        name = (name or "").lower()
        if list_key not in self.data:
            self.data[list_key] = []
        if name not in self.data[list_key]:
            self.data[list_key].append(name)
            self.save()

    def add_weapon(self, name, list_key):
        """Добавляет оружие в указанный список и сохраняет changes."""
        name = (name or "").lower()
        if list_key not in self.data:
            self.data[list_key] = []
        if name not in self.data[list_key]:
            self.data[list_key].append(name)
            self.save()

    def all_characters(self):
        """Все известные имена персонажей (объединение списков персонажей)."""
        result = []
        for key in config.CHARACTER_LISTS:
            result.extend(self.data.get(key, []))
        return result

    def all_weapons(self):
        """Все известные названия оружия."""
        result = []
        for key in config.WEAPON_LISTS:
            result.extend(self.data.get(key, []))
        return result