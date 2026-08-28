"""Пользовательский интерфейс приложения на Gradio.

Приложение «Genshin Sim Statistics» содержит две вкладки:
  - «Genshin DPS Leaders» — таблица лидеров отрядов по урону (база Simpact);
  - «Wfpsim database» — ведение локальной базы замеров урона из сервиса Wfpsim.

Выбор языка (русский / английский) вынесен на уровень всего интерфейса.
"""

import base64
import html

import gradio as gr

from . import (
    classifiers,
    config,
    downloader,
    filters,
    html_utils,
    i18n,
    models,
    update,
)
from .classifier_ui import (
    MAX_CLS_ROWS,
    cls_n_pages as _cls_n_pages,
    nav_updates as _nav_updates,
    row_reset_updates as _row_reset_updates,
    row_updates as _row_updates,
)
from .db import LocalDB
from .downloader import SimpactDownloader
from .objects_manager import ObjectsManager
from .wfpsim import ui as wfpsim_ui

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
   drop-shadow следует альфа-каналу, поэтому обводка идёт по периметру иконки.
   Применяется только к иконкам оружия. */
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
    more_link = i18n.t("link_more")
    art_title = i18n.t("art_title")

    card = [
        '<div style="border:1px solid #3f3f46;border-radius:10px;padding:14px;'
        'margin:10px 0;background:#252526;">',
        '<div style="display:flex;justify-content:space-between;align-items:center;">',
        f'<div style="font-size:22px;font-weight:bold;color:#5aa2e6;">DPS: {dps_str}</div>',
        f'<a href="{link}" target="_blank" style="text-decoration:none;background:#1f6fb2;'
        f'color:#fff;padding:8px 14px;border-radius:6px;">{more_link}</a>',
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

        # Иконка набора артефактов снизу-слева (поверх аватара).
        # При двух наборах — половинки иконок, разделённые по вертикали.
        arts = html_utils.artifact_icons_html(art_srcs, art_title)
        if arts:
            avatar_box += (
                '<div style="position:absolute;bottom:2px;left:2px;">' + arts + '</div>'
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

    # Комментарий к замеру между иконками и кнопкой
    desc = (record.get("description") or "").strip()
    if desc:
        card.append(
            '<div style="color:#9a9a9a;font-style:italic;margin-top:8px;'
            'border-top:1px dashed #3f3f46;padding-top:6px;">'
            + html.escape(desc) + '</div>'
        )

    card.append('</div>')
    return "".join(card)


# Внутренние идентификаторы наборов фильтров (значения выпадающего списка).
# Отображаемые названия локализованы через i18n и зависят от выбранного языка.
FILTER_ALL = "all"
FILTER_KQMS = "kqms"
FILTER_KQMS_SELECTOR = "kqms_selector"
FILTER_FTP = "ftp"


def filter_choices() -> list:
    """Локализованные варианты набора фильтров для выпадающего списка."""
    return [
        (i18n.t("filter_all"), FILTER_ALL),
        (i18n.t("filter_kqms"), FILTER_KQMS),
        (i18n.t("filter_kqms_selector"), FILTER_KQMS_SELECTOR),
        (i18n.t("filter_ftp"), FILTER_FTP),
    ]


def filter_records(ldb, om, filter_set, required, excluded):
    """Возвращает записи базы с учётом набора фильтров и персонажей."""
    records = ldb.sorted_records()
    if filter_set == FILTER_KQMS:
        records = [r for r in records if r.get("flags", {}).get("kqms")]
    elif filter_set == FILTER_KQMS_SELECTOR:
        records = [r for r in records if r.get("flags", {}).get("kqms_selector")]
    elif filter_set == FILTER_FTP:
        records = [r for r in records if r.get("flags", {}).get("ftp")]

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
    pages = max(1, (total + size - 1) // size)

    header = i18n.t("total_teams", total=total, page=page, pages=pages)
    parts = [f'<div style="color:#888;margin:6px 0;">{header}</div>']
    if not page_records:
        parts.append(
            '<div style="color:#999;padding:20px;">' + i18n.t("no_teams") + '</div>'
        )
    else:
        parts.extend(record_card_html(r, dl) for r in page_records)
    return "".join(parts), i18n.t("total_label", total=total)


# ---------------------------------------------------------------------------
# Обработчики событий
# ---------------------------------------------------------------------------

# Вспомогательные функции панели классификации импортируются из classifier_ui:
# MAX_CLS_ROWS, _cls_n_pages, _row_updates, _row_reset_updates, _nav_updates.

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
            msg = i18n.t(
                "update_done",
                fetched=stats["total_fetched"],
                merged=stats["merged"],
                skipped=stats["skipped"],
                total=stats["total_in_db"],
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
        msg = i18n.t("fetched_unknown", total=total)
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
        msg = i18n.t(
            "update_done",
            fetched=stats["total_fetched"],
            merged=stats["merged"],
            skipped=stats["skipped"],
            total=stats["total_in_db"],
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
# Вкладка «Genshin DPS Leaders»
# ---------------------------------------------------------------------------

def _build_dps_tab(om, ldb, dl, char_choices):
    """Строит содержимое вкладки «Genshin DPS Leaders» и возвращает описатель вкладки.

    Возвращаемый словарь содержит refresh/refresh_inputs/refresh_outputs,
    lang_outputs/update_lang.
    """
    with gr.Column():
        with gr.Row():
            update_btn = gr.Button(i18n.t("update_btn"), variant="primary")
        status = gr.Markdown(i18n.t("status_ready"))

        # Состояния двухэтапного обновления и пагинации классификатора
        raw_state = gr.State([])
        cls_items = gr.State([])
        cls_page = gr.State(0)

        # Панель классификации неизвестных объектов
        with gr.Column(visible=False) as unknown_group:
            cls_heading = gr.Markdown(i18n.t("cls_heading"))
            cls_description = gr.Markdown(i18n.t("cls_description"))
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
                        label=i18n.t("cls_list_label"),
                    )
                cls_rows.append({"row": row, "img": img, "name": name, "dd": dd})
            with gr.Row():
                cls_prev_btn = gr.Button(i18n.t("cls_prev"), visible=False, size="sm")
                cls_nav_label = gr.Markdown("", elem_id="cls_nav")
                cls_next_btn = gr.Button(i18n.t("cls_next"), visible=False, size="sm")
            apply_btn = gr.Button(
                i18n.t("cls_apply"), visible=False
            )

        # Обработчики зависят от динамически созданных строк классификации
        handlers = make_handlers(om, ldb, dl, cls_rows)

        filters_heading = gr.Markdown(i18n.t("filters_heading"))
        with gr.Row():
            filter_set = gr.Dropdown(
                choices=filter_choices(),
                value=FILTER_ALL,
                label=i18n.t("filter_set_label"),
            )
            page_size = gr.Dropdown(
                choices=[10, 20, 50],
                value=10,
                label=i18n.t("page_size_label"),
            )
        with gr.Row():
            required = gr.Dropdown(
                choices=char_choices,
                multiselect=True,
                label=i18n.t("required_label"),
            )
            excluded = gr.Dropdown(
                choices=char_choices,
                multiselect=True,
                label=i18n.t("excluded_label"),
            )

        teams_heading = gr.Markdown(i18n.t("teams_heading"))
        teams_html = gr.HTML()
        total_label = gr.Markdown("")

        with gr.Row():
            prev_btn = gr.Button(i18n.t("prev_btn"))
            page = gr.Number(value=1, precision=0, label=i18n.t("page_label"))
            next_btn = gr.Button(i18n.t("next_btn"))

        refresh_inputs = [filter_set, required, excluded, page, page_size]
        refresh_outputs = [teams_html, total_label]

        # Подписи компонентов, которые нужно обновить при смене языка
        lang_outputs = [
            update_btn, status,
            cls_heading, cls_description, apply_btn, cls_prev_btn, cls_next_btn,
            filter_set, page_size, required, excluded,
            filters_heading, teams_heading, prev_btn, page, next_btn,
        ]
        for r in cls_rows:
            lang_outputs.append(r["dd"])

        def update_lang(lang):
            """Возвращает обновления подписей вкладки при смене языка."""
            i18n.set_lang(lang)
            updates = [
                gr.update(value=i18n.t("update_btn")),
                gr.update(value=i18n.t("status_ready")),
                gr.update(value=i18n.t("cls_heading")),
                gr.update(value=i18n.t("cls_description")),
                gr.update(value=i18n.t("cls_apply")),
                gr.update(value=i18n.t("cls_prev")),
                gr.update(value=i18n.t("cls_next")),
                gr.update(label=i18n.t("filter_set_label"), choices=filter_choices()),
                gr.update(label=i18n.t("page_size_label")),
                gr.update(label=i18n.t("required_label")),
                gr.update(label=i18n.t("excluded_label")),
                gr.update(value=i18n.t("filters_heading")),
                gr.update(value=i18n.t("teams_heading")),
                gr.update(value=i18n.t("prev_btn")),
                gr.update(label=i18n.t("page_label")),
                gr.update(value=i18n.t("next_btn")),
            ]
            for _ in cls_rows:
                updates.append(gr.update(label=i18n.t("cls_list_label")))
            return updates

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

        # Фильтры: смена фильтра/сортировки сбрасывает список на первую страницу
        filter_set.change(lambda: 1, [], [page]).then(
            handlers["refresh"], refresh_inputs, refresh_outputs
        )
        required.change(lambda: 1, [], [page]).then(
            handlers["refresh"], refresh_inputs, refresh_outputs
        )
        excluded.change(lambda: 1, [], [page]).then(
            handlers["refresh"], refresh_inputs, refresh_outputs
        )
        page_size.change(lambda: 1, [], [page]).then(
            handlers["refresh"], refresh_inputs, refresh_outputs
        )
        page.change(handlers["refresh"], refresh_inputs, refresh_outputs)

        # Пагинация
        prev_btn.click(lambda p: max(1, int(p or 1) - 1), [page], [page]) \
            .then(handlers["refresh"], refresh_inputs, refresh_outputs)
        next_btn.click(lambda p: int(p or 1) + 1, [page], [page]) \
            .then(handlers["refresh"], refresh_inputs, refresh_outputs)

        # Обновление базы: сначала показываем явный индикатор начала,
        # затем запускаем длительную операцию и перерисовываем список.
        update_btn.click(
            lambda: gr.update(value=i18n.t("update_started")),
            [],
            [status],
        ).then(
            handlers["update"],
            inputs=refresh_inputs,
            outputs=cls_full_outputs,
        ).then(
            handlers["refresh"],
            refresh_inputs,
            refresh_outputs,
        )

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

    return {
        "refresh": handlers["refresh"],
        "refresh_inputs": refresh_inputs,
        "refresh_outputs": refresh_outputs,
        "lang_outputs": lang_outputs,
        "update_lang": update_lang,
    }


# ---------------------------------------------------------------------------
# Построение интерфейса
# ---------------------------------------------------------------------------

def build_demo():
    om = ObjectsManager()
    ldb = LocalDB()
    dl = SimpactDownloader()

    char_choices = sorted(set(om.all_characters()))
    lang_choices = [(i18n.LANG_LABELS[k], k) for k in i18n.LANGUAGES]

    with gr.Blocks(title=config.APP_NAME, css=APP_CSS, theme=make_dark_theme()) as demo:
        gr.Markdown("# ⚙️ " + i18n.t("app_title"))
        subtitle = gr.Markdown(i18n.t("app_subtitle"))

        # Общий выбор языка для всего интерфейса (обе вкладки)
        language = gr.Dropdown(
            choices=lang_choices,
            value=i18n.get_lang(),
            label=i18n.t("language_label"),
        )

        with gr.Tabs():
            with gr.Tab(i18n.t("tab_dps")):
                dps_tab = _build_dps_tab(om, ldb, dl, char_choices)
            with gr.Tab(i18n.t("tab_wfpsim")):
                wf_tab = wfpsim_ui.build_wfpsim_tab(om)

        # Первичное построение обеих вкладок
        demo.load(
            dps_tab["refresh"], dps_tab["refresh_inputs"], dps_tab["refresh_outputs"]
        )
        demo.load(
            wf_tab["refresh"], wf_tab["refresh_inputs"], wf_tab["refresh_outputs"]
        )

        # Смена языка (общий выбор для всего интерфейса)
        lang_outputs = [subtitle] + dps_tab["lang_outputs"] + wf_tab["lang_outputs"]

        def handle_language(lang):
            """Переключает язык и возвращает обновления подписей обеих вкладок."""
            i18n.set_lang(lang)
            updates = [gr.update(value=i18n.t("app_subtitle"))]
            updates += dps_tab["update_lang"](lang)
            updates += wf_tab["update_lang"](lang)
            return updates

        language.change(
            handle_language,
            [language],
            lang_outputs,
        ).then(
            dps_tab["refresh"], dps_tab["refresh_inputs"], dps_tab["refresh_outputs"]
        ).then(
            wf_tab["refresh"], wf_tab["refresh_inputs"], wf_tab["refresh_outputs"]
        )

    return demo