"""Общие HTML-вспомогательные функции для интерфейсов (карточки, изображения)."""

import base64
import html


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


def artifact_icons_html(art_srcs, title: str = "") -> str:
    """HTML иконок набора артефактов.

    При одном наборе возвращается одна иконка. При двух наборах иконки делятся
    пополам по вертикали (левая и правая половины одной позиции).
    ``art_srcs`` — список data-URI изображений (или путей); учитываются первые два.
    """
    srcs = [s for s in (art_srcs or []) if s][:2]
    if not srcs:
        return ""
    t = html.escape(title or "")
    if len(srcs) == 1:
        return (
            f'<img src="{srcs[0]}" class="icon-outline" '
            f'style="width:44px;height:44px;object-fit:cover;" title="{t}">'
        )
    # Два набора: левая половина первой иконки + правая половина второй,
    # склеенные в одной позиции и разделённые вертикальной линией.
    # Каждая иконка масштабируется до двойной ширины контейнера и прижимается
    # к нужному краю, чтобы в окне оставалась только требуемая половина.
    left = (
        '<div style="position:absolute;left:0;top:0;width:50%;height:100%;'
        'overflow:hidden;">'
        f'<img src="{srcs[0]}" class="icon-outline" style="width:200%;max-width:none;'
        'height:100%;object-fit:cover;display:block;position:absolute;'
        'left:0;top:0;" '
        f'title="{t}"></div>'
    )
    right = (
        '<div style="position:absolute;right:0;top:0;width:50%;height:100%;'
        'overflow:hidden;box-sizing:border-box;border-left:1px solid rgba(0,0,0,0.7);">'
        f'<img src="{srcs[1]}" class="icon-outline" style="width:200%;max-width:none;'
        'height:100%;object-fit:cover;display:block;position:absolute;'
        'right:0;top:0;" '
        f'title="{t}"></div>'
    )
    return (
        '<div style="width:44px;height:44px;position:relative;overflow:hidden;'
        'border-radius:2px;">' + left + right + '</div>'
    )