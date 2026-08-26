"""Пользовательский интерфейс приложения на Gradio."""

import base64
import html

import gradio as gr

from . import classifiers, config, downloader, filters, models, update
from .db import LocalDB
from .downloader import SimpactDownloader
from .objects_manager import ObjectsManager

APP_CSS = """
/* Более тёмный фон элементов выпадающих списков для тёмной темы */
.gradio-container ul.options li,
.gradio-container .options li.item,
.gradio-container .wrap li {
    background-color: #2e2e2e !important;
    color: #e6e6e6 !important;
}
.gradio-container ul.options li:hover,
.gradio-container .options li.item:hover {
    background-color: #3d3d3d !important;
}
.gradio-container ul.options li.selected,
.gradio-container .options li.item.selected {
    background-color: #1f6fb2 !important;
    color: #ffffff !important;
}
/* Белая обводка по контуру непрозрачной части изображения (не всего квадрата):
   drop-shadow следует альфа-каналу, поэтому обводка идёт по периметру иконки. */
.icon-outline {
    filter: drop-shadow(0 0 1px rgba(255, 255, 255, 0.9))
            drop-shadow(1px 0 0 rgba(255, 255, 255, 0.9))
            drop-shadow(-1px 0 0 rgba(255, 255, 255, 0.9))
            drop-shadow(0 1px 0 rgba(255, 255, 255, 0.9))
            drop-shadow(0 -1px 0 rgba(255, 255, 255, 0.9));
}
"""


def make_dark_theme():
    """Возвращает тёмную тему интерфейса (корректно затемняет списки)."""
    return gr.themes.Base().set(
        background_fill_primary="#1e1e1e",
        background_fill_secondary="#252526",
        body_background_fill="#1e1e1e",
        body_text_color="#d4d4d4",
        body_text_color_subdued="#9a9a9a",
        block_background_fill="#252526",
        block_border_color="#3f3f46",
        input_background_fill="#1b1b1b",
        input_border_color="#3f3f46",
        border_color_primary="#3f3f46",
        button_primary_background_fill="#1f6fb2",
        button_primary_text_color="#ffffff",
    )


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _img_src(path) -> str:
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


def record_card_html(record, dl: SimpactDownloader) -> str:
    """Строит HTML-карточку отряда с изображениями, cons/refine и ссылкой на gcsim."""
    link = config.GCSIM_DB_URL.format(record_id=record.get("_id", ""))
    dps_str = format_dps(record.get("mean_dps_per_target", 0))
    team_names = " · ".join(html.escape(m.get("name", "")) for m in record.get("team", []))

    card = [
        '<div style="border:1px solid #3f3f46;border-radius:10px;padding:14px;'
        'margin:10px 0;background:#252526;">',
        '<div style="display:flex;justify-content:space-between;align-items:center;">',
        f'<div style="font-size:22px;font-weight:bold;color:#5aa2e6;">DPS: {dps_str}</div>',
        f'<a href="{link}" target="_blank" style="text-decoration:none;background:#1f6fb2;'
        'color:#fff;padding:8px 14px;border-radius:6px;">Подробнее на gcsim</a>',
        '</div>',
        f'<div style="color:#9a9a9a;margin:6px 0;">{team_names}</div>',
    ]

    for m in record.get("team", []):
        assets = downloader.member_assets(dl, m, force=False)
        av = _img_src(assets["avatar"])
        wp = _img_src(assets["weapon"])
        art_srcs = [_img_src(p) for p in assets["artifacts"]]

        name_esc = html.escape(m.get("name", ""))
        cons = models.member_cons(m)
        refine = (m.get("weapon") or {}).get("refine")

        cell = ('<div style="display:inline-block;text-align:center;margin:8px;'
                'width:120px;vertical-align:top;">')

        # Контейнер аватара (увеличен в 2 раза) с наложенными элементами
        avatar_box = (
            '<div style="position:relative;display:inline-block;'
            'width:120px;height:120px;border-radius:8px;overflow:hidden;">'
        )
        if av:
            avatar_box += (f'<img src="{av}" style="width:120px;height:120px;'
                           'object-fit:cover;display:block;">')
        else:
            avatar_box += (f'<div style="width:120px;height:120px;background:#333;'
                           f'color:#bbb;display:flex;align-items:center;'
                           f'justify-content:center;">{name_esc}</div>')

        # cons сверху-слева и refine сразу справа от него (поверх аватара),
        # цвета поменяны местами: cons — золотой, refine — синий
        badges = ('<div style="position:absolute;top:2px;left:2px;display:flex;'
                  'align-items:center;gap:4px;background:rgba(15,15,15,0.75);'
                  'padding:1px 6px;border-radius:6px 0 6px 0;font-weight:bold;'
                  'font-size:13px;font-family:monospace;">'
                  f'<span style="color:#d9a441;">C{cons}</span>')
        if refine:
            badges += f'<span style="color:#5aa2e6;">R{refine}</span>'
        badges += '</div>'
        avatar_box += badges

        # Иконка набора артефактов снизу-слева (поверх аватара)
        if art_srcs:
            arts = "".join(
                f'<img src="{s}" class="icon-outline" style="width:44px;height:44px;'
                'object-fit:cover;border:1px solid #555;border-radius:4px;'
                'margin:1px;" title="Сет">'
                for s in art_srcs[:2]
            )
            avatar_box += (
                '<div style="position:absolute;bottom:2px;left:2px;display:flex;">'
                + arts + '</div>'
            )

        # Иконка оружия снизу-справа (поверх аватара)
        if wp:
            avatar_box += (
                '<div style="position:absolute;bottom:2px;right:2px;">'
                f'<img src="{wp}" class="icon-outline" style="width:52px;height:52px;'
                'object-fit:contain;">'
                '</div>'
            )

        avatar_box += '</div>'
        cell += avatar_box
        cell += f'<div style="font-weight:bold;margin-top:4px;">{name_esc}</div>'
        cell += '</div>'
        card.append(cell)

    # Задача 3: комментарий к замеру между иконками и кнопкой
    desc = (record.get("description") or "").strip()
    if desc:
        card.append(
            '<div style="color:#9a9a9a;font-style:italic;margin-top:8px;'
            'border-top:1px dashed #3f3f46;padding-top:6px;">'
            + html.escape(desc) + '</div>'
        )

    card.append('</div>')
    return "".join(card)


def filter_records(ldb, om, filter_set, required, excluded):
    """Возвращает записи базы с учётом набора фильтров и персонажей."""
    records = ldb.sorted_records()
    if filter_set == "KQMS":
        records = [r for r in records if r.get("flags", {}).get("kqms")]
    elif filter_set == "KQMS с селектором":
        records = [r for r in records if r.get("flags", {}).get("kqms_selector")]

    req = {x.lower() for x in (required or [])}
    exc = {x.lower() for x in (excluded or [])}

    def passes(rec):
        names = set(rec.get("names", []))
        if req and not names.issuperset(req):
            return False
        if exc and names.intersection(exc):
            return False
        return True

    return [r for r in records if passes(r)]


def build_teams_html(ldb, om, dl, filter_set, required, excluded, page, page_size):
    """Формирует HTML всех карточек отрядов для текущей страницы."""
    records = filter_records(ldb, om, filter_set, required, excluded)
    total = len(records)
    page = max(1, int(page))
    size = int(page_size)
    start = (page - 1) * size
    page_records = records[start:start + size]

    parts = [
        f'<div style="color:#888;margin:6px 0;">Всего отрядов: {total} · страница {page}'
        f' из {max(1, (total + size - 1) // size)}</div>'
    ]
    if not page_records:
        parts.append('<div style="color:#999;padding:20px;">Нет отрядов, соответствующих фильтрам.</div>')
    else:
        parts.extend(record_card_html(r, dl) for r in page_records)
    return "".join(parts), f"Всего отрядов: {total}"


# ---------------------------------------------------------------------------
# Обработчики событий
# ---------------------------------------------------------------------------

MAX_CLS_ROWS = 15  # количество объектов классификатора на одной странице


def _cls_n_pages(items, size):
    return max(1, (len(items) + size - 1) // size)


def _row_updates(cls_rows, items, page, dl, assign, selections=None):
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


def _row_reset_updates(cls_rows, assign, selections=None):
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


def _nav_updates(items, page, size):
    """gr.update для кнопок навигации и метки страницы."""
    n_pages = _cls_n_pages(items, size)
    page = min(max(0, page), n_pages - 1)
    if n_pages > 1:
        prev = gr.update(visible=True, interactive=page > 0)
        nxt = gr.update(visible=True, interactive=page < n_pages - 1)
    else:
        prev = gr.update(visible=False)
        nxt = gr.update(visible=False)
    label = gr.update(value=f"Стр. {page + 1} из {n_pages}")
    return prev, nxt, label, page


def make_handlers(om, ldb, dl, cls_rows=None):
    """Возвращает словарь функций-обработчиков, замыкающих состояние."""
    cls_assign = {}
    cls_map = {}
    size = len(cls_rows or [])

    def handle_refresh(filter_set, required, excluded, page, page_size):
        return build_teams_html(ldb, om, dl, filter_set, required, excluded, page, page_size)

    def handle_update(filter_set, required, excluded, page, page_size,
                      progress=gr.Progress()):
        config.ensure_cache_dirs()
        raw, collector, total = update.fetch_phase(dl, om, progress)
        if collector.is_empty():
            stats = update.finalize_phase(
                raw, om, ldb, dl, {}, {}, progress=progress
            )
            msg = (
                f"Обновление завершено: выгружено {stats['total_fetched']}, "
                f"в базу добавлено/обновлено {stats['merged']}, "
                f"пропущено {stats['skipped']}. Всего в базе: {stats['total_in_db']}."
            )
            row_u = _row_reset_updates(cls_rows, cls_assign, cls_map)
            tail = [
                gr.update(visible=False),  # cls_prev_btn
                gr.update(visible=False),  # cls_next_btn
                gr.update(value=""),       # cls_nav_label
                gr.update(visible=False),  # apply_btn
                [], 0, [],                 # cls_items, cls_page, raw_state
                msg,                       # status
                gr.update(visible=False),  # unknown_group
            ]
            return row_u + tail
        items = collector.items()
        row_u = _row_updates(cls_rows, items, 0, dl, cls_assign, cls_map)
        prev, nxt, label, _ = _nav_updates(items, 0, size)
        msg = (
            f"Выгружено {total} записей. Обнаружены неизвестные объекты — "
            "укажите список классификации для каждого и нажмите «Применить»."
        )
        tail = [
            prev, nxt, label,
            gr.update(visible=True),       # apply_btn
            items, 0, raw,                 # cls_items, cls_page, raw_state
            msg,                           # status
            gr.update(visible=True),       # unknown_group
        ]
        return row_u + tail

    def handle_cls_prev(page, items):
        items = items or []
        new_page = max(0, int(page or 0) - 1)
        row_u = _row_updates(cls_rows, items, new_page, dl, cls_assign, cls_map)
        prev, nxt, label, _ = _nav_updates(items, new_page, size)
        return row_u + [prev, nxt, label, new_page]

    def handle_cls_next(page, items):
        items = items or []
        n_pages = _cls_n_pages(items, size)
        new_page = min(int(page or 0) + 1, n_pages - 1)
        row_u = _row_updates(cls_rows, items, new_page, dl, cls_assign, cls_map)
        prev, nxt, label, _ = _nav_updates(items, new_page, size)
        return row_u + [prev, nxt, label, new_page]

    def handle_apply(*args, progress=gr.Progress()):
        items = args[size] or []
        char_map = {}
        weapon_map = {}
        # Применяем классификации для ВСЕХ объектов (со всех страниц).
        # Для объектов без явного выбора используем рекомендованный список.
        for gi, (kind, name) in enumerate(items):
            val = cls_map.get(gi) or classifiers.recommended_list(kind)
            if not val:
                continue
            if kind == "char":
                char_map[name] = val
            else:
                weapon_map[name] = val
        stats = update.finalize_phase(
            args[size + 2], om, ldb, dl, char_map, weapon_map, progress=progress
        )
        msg = (
            f"Обновление завершено: выгружено {stats['total_fetched']}, "
            f"в базу добавлено/обновлено {stats['merged']}, "
            f"пропущено {stats['skipped']}. Всего в базе: {stats['total_in_db']}."
        )
        row_u = _row_reset_updates(cls_rows, cls_assign, cls_map)
        tail = [
            gr.update(visible=False), gr.update(visible=False), gr.update(value=""),
            gr.update(visible=False), [], 0, [],
            msg, gr.update(visible=False),
        ]
        return row_u + tail

    def handle_cls_select(row_idx):
        """Возвращает обработчик выбора списка для строки классификатора."""

        def inner(value, items, page):
            items = items or []
            gi = int(page or 0) * size + row_idx
            if gi < len(items):
                if value:
                    cls_map[gi] = value
                else:
                    cls_map.pop(gi, None)
            return gr.update(value=value)

        return inner

    return {
        "refresh": handle_refresh,
        "update": handle_update,
        "cls_prev": handle_cls_prev,
        "cls_next": handle_cls_next,
        "apply": handle_apply,
        "select": [handle_cls_select(i) for i in range(size)],
    }


# ---------------------------------------------------------------------------
# Построение интерфейса
# ---------------------------------------------------------------------------

def build_demo():
    om = ObjectsManager()
    ldb = LocalDB()
    dl = SimpactDownloader()

    char_choices = sorted(set(om.all_characters()))
    filter_choices = ["Все отряды", "KQMS", "KQMS с селектором"]

    with gr.Blocks(title="Genshin DPS leaders", css=APP_CSS, theme=make_dark_theme()) as demo:
        gr.Markdown("# ⚔️ Genshin DPS leaders")
        gr.Markdown(
            "Таблица лидеров отрядов по урону. Данные обновляются из базы Simpact."
        )

        with gr.Row():
            update_btn = gr.Button("Обновить локальную базу", variant="primary")
        status = gr.Markdown("Локальная база готова.")

        # Состояния двухэтапного обновления и пагинации классификатора
        raw_state = gr.State([])
        cls_items = gr.State([])
        cls_page = gr.State(0)

        # Панель классификации неизвестных объектов
        with gr.Column(visible=False) as unknown_group:
            gr.Markdown("### Классификация неизвестных объектов")
            gr.Markdown(
                "Для каждого объекта выберите список классификации из выпадающего "
                "меню и нажмите «Применить». Для оружия показывается его изображение."
            )
            cls_rows = []
            for _ in range(MAX_CLS_ROWS):
                with gr.Row(visible=False) as row:
                    img = gr.Image(
                        width=48,
                        height=48,
                        show_label=False,
                        container=False,
                    )
                    name = gr.Markdown("")
                    dd = gr.Dropdown(
                        choices=config.ALL_LISTS,
                        interactive=True,
                        label="Список",
                    )
                cls_rows.append({"row": row, "img": img, "name": name, "dd": dd})
            with gr.Row():
                cls_prev_btn = gr.Button("◀ Пред.", visible=False, size="sm")
                cls_nav_label = gr.Markdown("", elem_id="cls_nav")
                cls_next_btn = gr.Button("След. ▶", visible=False, size="sm")
            apply_btn = gr.Button(
                "Применить классификацию и продолжить", visible=False
            )

        # Обработчики зависят от динамически созданных строк классификации
        handlers = make_handlers(om, ldb, dl, cls_rows)

        gr.Markdown("### Фильтры")
        with gr.Row():
            filter_set = gr.Dropdown(
                choices=filter_choices,
                value="Все отряды",
                label="Набор фильтров",
            )
            page_size = gr.Dropdown(
                choices=[10, 20, 50],
                value=10,
                label="Отрядов на странице",
            )
        with gr.Row():
            required = gr.Dropdown(
                choices=char_choices,
                multiselect=True,
                label="Обязательные персонажи (все должны быть в отряде)",
            )
            excluded = gr.Dropdown(
                choices=char_choices,
                multiselect=True,
                label="Исключённые персонажи (ни один не должен встречаться)",
            )

        gr.Markdown("### Отряды")
        teams_html = gr.HTML()
        total_label = gr.Markdown("")

        with gr.Row():
            prev_btn = gr.Button("◀ Назад")
            page = gr.Number(value=1, precision=0, label="Страница")
            next_btn = gr.Button("Вперёд ▶")

        refresh_inputs = [filter_set, required, excluded, page, page_size]
        refresh_outputs = [teams_html, total_label]

        # Первичное отображение
        demo.load(
            handlers["refresh"],
            inputs=refresh_inputs,
            outputs=refresh_outputs,
        )

        # Фильтры
        filter_set.change(handlers["refresh"], refresh_inputs, refresh_outputs)
        required.change(handlers["refresh"], refresh_inputs, refresh_outputs)
        excluded.change(handlers["refresh"], refresh_inputs, refresh_outputs)
        page_size.change(handlers["refresh"], refresh_inputs, refresh_outputs)
        page.change(handlers["refresh"], refresh_inputs, refresh_outputs)

        # Пагинация
        prev_btn.click(lambda p: max(1, int(p or 1) - 1), [page], [page]) \
            .then(handlers["refresh"], refresh_inputs, refresh_outputs)
        next_btn.click(lambda p: int(p or 1) + 1, [page], [page]) \
            .then(handlers["refresh"], refresh_inputs, refresh_outputs)

        cls_outputs = []
        for r in cls_rows:
            cls_outputs += [r["row"], r["img"], r["name"], r["dd"]]

        cls_full_outputs = cls_outputs + [
            cls_prev_btn, cls_next_btn, cls_nav_label,
            apply_btn, cls_items, cls_page, raw_state, status, unknown_group,
        ]
        cls_nav_outputs = cls_outputs + [
            cls_prev_btn, cls_next_btn, cls_nav_label, cls_page,
        ]

        # Обновление базы
        update_btn.click(
            handlers["update"],
            inputs=refresh_inputs,
            outputs=cls_full_outputs,
        ).then(handlers["refresh"], refresh_inputs, refresh_outputs)

        # Навигация по страницам классификатора
        cls_prev_btn.click(
            handlers["cls_prev"], inputs=[cls_page, cls_items], outputs=cls_nav_outputs
        )
        cls_next_btn.click(
            handlers["cls_next"], inputs=[cls_page, cls_items], outputs=cls_nav_outputs
        )

        # Применение классификации
        apply_btn.click(
            handlers["apply"],
            inputs=[r["dd"] for r in cls_rows] + [cls_items, cls_page, raw_state],
            outputs=cls_full_outputs,
        ).then(handlers["refresh"], refresh_inputs, refresh_outputs)

        # Сохранение выбранных списков при переключении страниц классификатора,
        # чтобы при применении учитывались классификации со всех страниц
        for i, r in enumerate(cls_rows):
            r["dd"].change(
                handlers["select"][i],
                inputs=[r["dd"], cls_items, cls_page],
                outputs=[r["dd"]],
            )

    return demo