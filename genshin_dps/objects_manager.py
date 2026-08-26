"""Работа с objects.json: загрузка, сохранение и классификация объектов.

``objects.json`` хранится в папке ``cache/`` (``config.OBJECTS_PATH``). При первом
запуске, если файла в кэше ещё нет, он копируется из резервной копии рядом с
приложением/.exe (``config.DEFAULT_OBJECTS_PATH``), поставляемой через build.py.

Классификация объектов из замеров Wfpsim ведётся в отдельный файл
``cache/wfpsim_objects.json`` с той же структурой, что и ``objects.json``.
Для объединения списков используется ``UnionObjectsManager``: чтение выполняется
из обоих файлов, запись — только во второй (wfpsim_objects.json).
"""

import json
import shutil
from pathlib import Path

from . import config


class ObjectsManager:
    """Управляет классификационными списками персонажей и оружия в objects.json."""

    def __init__(self, path=None, seed_from_default=True):
        self.path = path or config.OBJECTS_PATH
        # Резервное копирование из DEFAULT_OBJECTS_PATH выполняется только для
        # основного objects.json. Для дополнительных файлов (wfpsim_objects.json)
        # оно отключено, чтобы они не заполнялись базовыми списками.
        self.seed_from_default = seed_from_default
        self.data = self.load()

    def load(self):
        """Загружает objects.json; при отсутствии создаёт пустую структуру.

        Если файла в кэше нет, а рядом с приложением есть резервная копия
        (``DEFAULT_OBJECTS_PATH``) и ``seed_from_default`` включён, она копируется
        в кэш.
        """
        path = Path(self.path)
        if self.seed_from_default and not path.exists():
            default = Path(config.DEFAULT_OBJECTS_PATH)
            if default.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(default, path)
                except OSError:
                    pass
        try:
            with open(path, "r", encoding="utf-8") as f:
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
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
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


class UnionObjectsManager:
    """Объединяет объекты из двух менеджеров (базового и дополнительного).

    Классификация (чтение) выполняется сначала по базовому файлу, затем по
    дополнительному. Запись новых классификаций идёт только в дополнительный
    файл (например, ``wfpsim_objects.json``), не затрагивая базовый.
    """

    def __init__(self, base, extra):
        self.base = base
        self.extra = extra

    def classify_character(self, name):
        cls = self.base.classify_character(name)
        if cls is None:
            cls = self.extra.classify_character(name)
        return cls

    def classify_weapon(self, name):
        cls = self.base.classify_weapon(name)
        if cls is None:
            cls = self.extra.classify_weapon(name)
        return cls

    def add_character(self, name, list_key):
        self.extra.add_character(name, list_key)

    def add_weapon(self, name, list_key):
        self.extra.add_weapon(name, list_key)

    def all_characters(self):
        result = set(self.base.all_characters())
        result.update(self.extra.all_characters())
        return sorted(result)

    def all_weapons(self):
        result = set(self.base.all_weapons())
        result.update(self.extra.all_weapons())
        return sorted(result)