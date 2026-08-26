"""Общие вспомогательные функции панели классификации неизвестных объектов.

Используются как во вкладке «Genshin DPS Leaders», так и во вкладке
«Wfpsim database» (для неизвестных персонажей/оружия из замеров Wfpsim).
"""

import gradio as gr

from . import classifiers, i18n

MAX_CLS_ROWS = 15  # количество объектов классификатора на одной странице


def cls_n_pages(items, size):
    return max(1, (len(items) + size - 1) // size)


def row_updates(cls_rows, items, page, dl, assign, selections=None):
    """gr.update для строк классификации по указанной странице."""
    selections = selections if selections is not None else {}
    start = max(0, page) * len(cls_rows)
    updates = []
    for i, r in enumerate(cls_rows):
        gi = start + i
        if gi < len(items):
            kind, name = items[gi]
            img_path = (
                dl.download_weapon(name)
                if kind == "weapon"
                else dl.download_avatar(name)
            )
            chosen = selections.get(gi)
            dd_val = chosen if chosen else classifiers.recommended_list(kind)
            updates.append(gr.update(visible=True))
            updates.append(gr.update(value=str(img_path) if img_path else None))
            updates.append(gr.update(value=name))
            updates.append(
                gr.update(
                    choices=classifiers.choices_for(kind),
                    value=dd_val,
                )
            )
            assign[gi] = (kind, name)
        else:
            updates.append(gr.update(visible=False))
            updates.append(gr.update(value=None))
            updates.append(gr.update(value=""))
            updates.append(gr.update(value=None))
            assign.pop(gi, None)
    return updates


def row_reset_updates(cls_rows, assign, selections=None):
    updates = []
    for _ in cls_rows:
        updates.append(gr.update(visible=False))
        updates.append(gr.update(value=None))
        updates.append(gr.update(value=""))
        updates.append(gr.update(value=None))
    assign.clear()
    if selections is not None:
        selections.clear()
    return updates


def nav_updates(items, page, size):
    """gr.update для кнопок навигации и метки страницы."""
    n_pages = cls_n_pages(items, size)
    page = min(max(0, page), n_pages - 1)
    if n_pages > 1:
        prev = gr.update(visible=True, interactive=page > 0)
        nxt = gr.update(visible=True, interactive=page < n_pages - 1)
    else:
        prev = gr.update(visible=False)
        nxt = gr.update(visible=False)
    label = gr.update(value=i18n.t("nav_page", page=page + 1, pages=n_pages))
    return prev, nxt, label, page