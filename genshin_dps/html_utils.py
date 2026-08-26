"""Общие HTML-вспомогательные функции для интерфейсов (карточки, изображения)."""

import base64


def img_src(path) -> str:
    """Возвращает data-URI изображения для вставки в HTML."""
    if not path:
        return ""
    try:
        if hasattr(path, "read_bytes"):
            data = path.read_bytes()
        else:
            with open(path, "rb") as f:
                data = f.read()
        return "data:image/png;base64," + base64.b64encode(data).decode()
    except Exception:
        return ""


def format_dps(value) -> str:
    """Форматирует DPS с разделителями тысяч через пробел."""
    return f"{int(value or 0):,}".replace(",", " ")