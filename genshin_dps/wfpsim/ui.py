"""Пользовательский интерфейс вкладки «Wfpsim database».

Вкладка предоставляет функционал создания, редактирования и удаления записей
замеров урона из базы Wfpsim. Записи хранятся в отдельной локальной базе
(``cache/wfpsim_db.json``), не смешиваясь с базой Simpact.

Замеры Wfpsim могут содержать персонажей и оружие, отсутствующие в objects.json.
В этом случае при добавлении/замене записи открывается панель классификации
(аналогичная таковой во вкладке «Genshin DPS Leaders»); результаты записываются
в отдельный файл ``cache/wfpsim_objects.json`` той же структуры, что и objects.json.
При фильтрации по персонажам используются объединённые списки обоих файлов.
"""

import html

import gradio as gr

from .. import classifiers, config, html_utils, i18n, models
from ..classifier_ui import (
    MAX_CLS_ROWS,
    cls_n_pages as _cls_n_pages,
    nav_updates as _nav_updates,
    row_reset_updates as _row_reset_updates,
    row_updates as _row_updates,
)
from ..objects_manager import ObjectsManager, UnionObjectsManager
from .db import WfpsimDB
from .service import NoResultsError, WfpsimService

# Копирование конфига в буфер обмена на клиентской стороне.
# Обрабатываем и значение напрямую, и массив входных значений (зависит от версии
# Gradio/числа входов), чтобы в буфер попадал полный текст, а не первый символ.
JS_COPY_CLIPBOARD = """
(x) => {
    const arr = Array.isArray(x);
    let text = arr ? (x && x[0]) : x;
    text = (text === undefined || text === null) ? "" : String(text);
    if (text && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(() => {});
    }
    return arr ? x : [x];
}
"""


# --- Построение HTML-карточки замера -------------------------------------

def _record_card_html(record: dict, service: WfpsimService) -> str:
    """Строит HTML-карточку замера (DPS, персонажи, аватары, оружие, артефакты)."""
    dps_str = html_utils.format_dps(record.get("mean_dps_per_target", 0))
    team_names = " · ".join(
        html.escape(m.get("name", "")) for m in record.get("team", [])
    )
    art_title = i18n.t("art_title")

    card = [
        '<div style="border:1px solid #3f3f46;border-radius:10px;padding:14px;'
        'margin:8px 0;background:#252526;">',
        '<div style="display:flex;justify-content:space-between;align-items:center;">',
        f'<div style="font-size:22px;font-weight:bold;color:#5aa2e6;">DPS: {dps_str}</div>',
    ]
    id_part = (
        f'<div style="font-size:12px;color:#777;">'
        f'{html.escape(str(record.get("_id", "")))}</div>'
    )
    if record.get("not_valid"):
        badge = (
            '<span style="background:#c0392b;color:#fff;padding:2px 8px;'
            'border-radius:4px;font-weight:bold;font-size:12px;">not valid</span>'
        )
        card.append(
            f'<div style="display:flex;align-items:center;gap:8px;">{badge}{id_part}</div>'
        )
    else:
        card.append(id_part)
    card.append('</div>')
    card.append(f'<div style="color:#9a9a9a;margin:6px 0;">{team_names}</div>')

    for m in record.get("team", []):
        av = html_utils.img_src(service.avatar_path(m))
        wp = html_utils.img_src(service.weapon_path(m))
        art_srcs = [html_utils.img_src(p) for p in service.artifact_paths(m)]

        name_esc = html.escape(m.get("name", ""))
        cons = models.member_cons(m)
        refine = (m.get("weapon") or {}).get("refine")

        cell = ('<div style="display:inline-block;text-align:center;margin:8px;'
                'width:120px;vertical-align:top;">')
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

        badges = ('<div style="position:absolute;top:2px;left:2px;display:flex;'
                  'align-items:center;gap:4px;background:rgba(15,15,15,0.75);'
                  'padding:1px 6px;border-radius:6px 0 6px 0;font-weight:bold;'
                  'font-size:13px;font-family:monospace;">'
                  f'<span style="color:#d9a441;">C{cons}</span>')
        if refine:
            badges += f'<span style="color:#5aa2e6;">R{refine}</span>'
        badges += '</div>'
        avatar_box += badges

        arts = html_utils.artifact_icons_html(art_srcs, art_title)
        if arts:
            avatar_box += (
                '<div style="position:absolute;bottom:2px;left:2px;">' + arts + '</div>'
            )

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

    desc = (record.get("description") or "").strip()
    if desc:
        card.append(
            '<div style="color:#9a9a9a;font-style:italic;margin-top:8px;">'
            + html.escape(desc) + '</div>'
        )

    card.append('</div>')
    return "".join(card)


def _more_html(url: str) -> str:
    """HTML-ссылка «Подробнее на wfpsim», оформленная как кнопка."""
    if not url:
        return ""
    text = html.escape(i18n.t("wf_link_more"))
    return (
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener" '
        'style="text-decoration:none;background:#1f6fb2;color:#fff;'
        'padding:8px 14px;border-radius:6px;display:inline-block;">'
        f'{text}</a>'
    )


# --- Сортировка и фильтрация ---------------------------------------------

WF_SORT_DATE = "date"
WF_SORT_DPS = "dps"


def wf_sort_choices():
    return [
        (i18n.t("wf_sort_date"), WF_SORT_DATE),
        (i18n.t("wf_sort_dps"), WF_SORT_DPS),
    ]


def _apply_filters(records, sort_key, required, excluded, show_invalid):
    if sort_key == WF_SORT_DPS:
        records = sorted(
            records,
            key=lambda r: r.get("mean_dps_per_target", 0),
            reverse=True,
        )
    else:
        records = sorted(
            records,
            key=lambda r: r.get("created_at", ""),
            reverse=True,
        )

    req = {x.lower() for x in (required or [])}
    exc = {x.lower() for x in (excluded or [])}

    result = []
    for rec in records:
        if not show_invalid and rec.get("not_valid"):
            continue
        names = set(rec.get("names", []))
        if req and not names.issuperset(req):
            continue
        if exc and names.intersection(exc):
            continue
        result.append(rec)
    return result


# --- Построение вкладки ----------------------------------------------------

def build_wfpsim_tab(om):
    """Строит содержимое вкладки «Wfpsim database» и возвращает описатель вкладки.

    ``om`` — базовый менеджер объектов (objects.json). Вместе с ним используется
    дополнительный менеджер wfpsim_objects.json через ``UnionObjectsManager``.

    Возвращаемый словарь содержит:
      - refresh / refresh_inputs / refresh_outputs — первичное построение списка;
      - lang_outputs / update_lang — обновление подписей при смене языка.
    """
    wdb = WfpsimDB()
    service = WfpsimService()

    # Объединённые списки: objects.json (базовый) + wfpsim_objects.json (дополнительный).
    # Дополнительный файл не наследует содержимое objects.json — он заполняется
    # только классификацией объектов из замеров Wfpsim.
    extra_om = ObjectsManager(config.WFPSIM_OBJECTS_PATH, seed_from_default=False)
    wom = UnionObjectsManager(om, extra_om)

    char_choices = wom.all_characters()
    # Число записей на странице выбирается пользователем (как во вкладке Simpact).
    PAGE_SIZE_CHOICES = [10, 20, 50]
    MAX_PAGE_SIZE = max(PAGE_SIZE_CHOICES)
    cls_size = MAX_CLS_ROWS

    # Состояние вкладки
    wf_records = gr.State([])
    wf_page = gr.State(1)
    wf_replace_target = gr.State(None)
    wf_clipboard = gr.Textbox(visible=False)
    # Состояние ожидающей классификации записи
    wf_pending_record = gr.State(None)
    wf_pending_old_id = gr.State(None)
    wf_cls_items = gr.State([])
    wf_cls_page = gr.State(0)

    gr.Markdown(i18n.t("wf_heading"))
    with gr.Row():
        wf_add_btn = gr.Button(i18n.t("wf_add_btn"), variant="primary")
        wf_status = gr.Markdown(i18n.t("wf_status_ready"))

    # Окно ввода ссылки (используется и для добавления, и для замены ссылки)
    with gr.Group(visible=False) as wf_dialog:
        dialog_heading = gr.Markdown(i18n.t("wf_dialog_heading"))
        wf_url = gr.Textbox(
            label=i18n.t("wf_url_label"),
            placeholder=i18n.t("wf_dialog_hint"),
        )
        with gr.Row():
            wf_continue_btn = gr.Button(i18n.t("wf_continue_btn"), variant="primary")
            wf_cancel_btn = gr.Button(i18n.t("wf_cancel_btn"))

    with gr.Row():
        wf_sort = gr.Dropdown(
            choices=wf_sort_choices(),
            value=WF_SORT_DATE,
            label=i18n.t("wf_sort_label"),
        )
    with gr.Row():
        wf_required = gr.Dropdown(
            choices=char_choices,
            multiselect=True,
            label=i18n.t("required_label"),
        )
        wf_excluded = gr.Dropdown(
            choices=char_choices,
            multiselect=True,
            label=i18n.t("excluded_label"),
        )
    with gr.Row():
        wf_show_invalid = gr.Checkbox(
            value=False,
            label=i18n.t("wf_show_invalid"),
        )
        wf_page_size = gr.Dropdown(
            choices=PAGE_SIZE_CHOICES,
            value=10,
            label=i18n.t("wf_page_size_label"),
        )
    wf_total_label = gr.Markdown("")

    # Панель классификации неизвестных персонажей/оружия из замеров Wfpsim.
    # Располагается над списком записей, чтобы при добавлении новой записи
    # открываться непосредственно перед списком отранжированных записей.
    with gr.Column(visible=False) as wf_unknown_group:
        wf_cls_heading = gr.Markdown(i18n.t("cls_heading"))
        wf_cls_description = gr.Markdown(i18n.t("cls_description"))
        wf_cls_rows = []
        wf_cls_row_outputs = []
        for _ in range(cls_size):
            with gr.Row(visible=False) as row:
                img = gr.Image(width=48, height=48, show_label=False, container=False)
                name = gr.Markdown("")
                dd = gr.Dropdown(
                    choices=config.ALL_LISTS,
                    interactive=True,
                    label=i18n.t("cls_list_label"),
                )
            wf_cls_rows.append({"row": row, "img": img, "name": name, "dd": dd})
            wf_cls_row_outputs += [row, img, name, dd]
        with gr.Row():
            wf_cls_prev_btn = gr.Button(i18n.t("cls_prev"), visible=False, size="sm")
            wf_cls_nav_label = gr.Markdown("", elem_id="wf_cls_nav")
            wf_cls_next_btn = gr.Button(i18n.t("cls_next"), visible=False, size="sm")
        wf_cls_apply_btn = gr.Button(i18n.t("cls_apply"), visible=False)

    # Карточки замеров (максимальное количество слотов; лишние скрываются
    # в зависимости от выбранного числа записей на странице)
    slots = []
    slot_outputs = []
    for _ in range(MAX_PAGE_SIZE):
        with gr.Column(visible=False) as col:
            card_html_comp = gr.HTML()
            with gr.Row():
                more = gr.HTML()
                replace_btn = gr.Button(i18n.t("wf_btn_replace"), size="sm")
                delete_btn = gr.Button(i18n.t("wf_btn_delete"), size="sm")
                invalid_btn = gr.Button(i18n.t("wf_btn_invalid"), size="sm")
                copy_btn = gr.Button(i18n.t("wf_btn_copy"), size="sm")
        slot = {
            "col": col,
            "html": card_html_comp,
            "more": more,
            "replace": replace_btn,
            "delete": delete_btn,
            "invalid": invalid_btn,
            "copy": copy_btn,
        }
        slots.append(slot)
        slot_outputs += [
            col, card_html_comp, more, replace_btn, delete_btn, invalid_btn, copy_btn,
        ]

    # Пагинация (включая переход к странице по номеру)
    with gr.Row():
        wf_prev_btn = gr.Button(i18n.t("wf_prev"))
        wf_page_num = gr.Number(value=1, precision=0, label=i18n.t("page_label"))
        wf_next_btn = gr.Button(i18n.t("wf_next"))
        wf_nav_label = gr.Markdown("")

    # Замыкаемое состояние классификатора (сопоставление строк с объектами)
    cls_assign = {}
    cls_map = {}

    # --- Внутренние вспомогательные функции ---

    def _build_current(sort_key, required, excluded, show_invalid, page_size, page):
        records = _apply_filters(
            wdb.records, sort_key, required, excluded, show_invalid
        )
        n = len(records)
        size = int(page_size or 10)
        total_pages = max(1, (n + size - 1) // size)
        page = min(max(1, int(page or 1)), total_pages)
        start = (page - 1) * size
        page_records = records[start:start + size]

        slot_updates = []
        for idx in range(MAX_PAGE_SIZE):
            if idx < len(page_records):
                rec = page_records[idx]
                # Исходная ссылка на запись Wfpsim (сохранённая при добавлении/замене)
                url = rec.get("wfpsim_url") or config.WFPSIM_SHARE_URL.format(
                    record_id=rec.get("_id")
                )
                slot_updates += [
                    gr.update(visible=True),
                    gr.update(value=_record_card_html(rec, service)),
                    gr.update(value=_more_html(url)),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                ]
            else:
                slot_updates += [
                    gr.update(visible=False),
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                ]

        if n == 0:
            total_text = i18n.t("wf_empty")
        else:
            total_text = i18n.t("wf_total", total=n)

        nav_updates = [
            gr.update(interactive=page > 1),
            gr.update(interactive=page < total_pages),
            gr.update(value=page),
            gr.update(value=i18n.t("wf_nav", page=page, pages=total_pages)),
        ]
        return records, page, slot_updates, nav_updates, total_text

    def _refresh_tail(sort_key, required, excluded, show_invalid, page_size, page):
        """Обновления карточек/пагинации/состояния списка."""
        records, page_used, slot_up, nav_up, total = _build_current(
            sort_key, required, excluded, show_invalid, page_size, page
        )
        return slot_up + nav_up + [page_used, records, total]

    def _cls_reset():
        """Обновления панели классификации для скрытого состояния."""
        row_u = _row_reset_updates(wf_cls_rows, cls_assign, cls_map)
        return row_u + [
            gr.update(visible=False),   # cls_prev_btn
            gr.update(visible=False),   # cls_next_btn
            gr.update(value=""),        # cls_nav_label
            [], 0,                      # cls_items, cls_page
            gr.update(visible=False),   # apply_btn
            gr.update(visible=False),   # unknown_group
        ]

    def _cls_show(items):
        """Обновления панели классификации для отображения неизвестных объектов."""
        row_u = _row_updates(wf_cls_rows, items, 0, service.dl, cls_assign, cls_map)
        prev, nxt, label, _ = _nav_updates(items, 0, cls_size)
        return row_u + [
            prev, nxt, label,
            items, 0,                   # cls_items, cls_page
            gr.update(visible=True),    # apply_btn
            gr.update(visible=True),    # unknown_group
        ]

    # --- Обработчики ---

    def handle_refresh(sort_key, required, excluded, show_invalid, page_size, page):
        return _refresh_tail(sort_key, required, excluded, show_invalid, page_size, page)

    def _slot_record(records, page, page_size, slot_idx):
        records = records or []
        page = max(1, int(page or 1))
        size = int(page_size or 10)
        idx = (page - 1) * size + slot_idx
        if 0 <= idx < len(records):
            return records[idx]
        return None

    def make_action(slot_idx, kind):
        def inner(sort_key, required, excluded, show_invalid, page_size, page, records):
            rec = _slot_record(records, page, page_size, slot_idx)
            if rec is not None:
                rid = rec.get("_id")
                if kind == "delete":
                    wdb.delete(rid)
                elif kind == "invalid":
                    wdb.toggle_not_valid(rid)
            return _refresh_tail(
                sort_key, required, excluded, show_invalid, page_size, page
            )
        return inner

    def make_copy(slot_idx):
        def inner(page, page_size, records):
            rec = _slot_record(records, page, page_size, slot_idx)
            cfg = rec.get("config", "") if rec else ""
            return cfg, i18n.t("wf_copied")
        return inner

    def make_replace_open(slot_idx):
        def inner(page, page_size, records):
            rec = _slot_record(records, page, page_size, slot_idx)
            rid = rec.get("_id") if rec else None
            return (
                rid,                         # wf_replace_target (State — сырое значение)
                gr.update(visible=True),     # wf_dialog
                gr.update(value=""),         # wf_url
            )
        return inner

    def handle_add_open():
        return None, gr.update(visible=True), gr.update(value="")

    def handle_cancel():
        return None, gr.update(visible=False)

    def _scan_unknowns(record):
        """Возвращает список (тип, имя) неизвестных объектов в составе записи."""
        collector = classifiers.UnknownCollector(wom)
        collector.scan_record({"summary": {"team": record.get("team", [])}})
        return collector.items()

    def _error_return(msg, sort_key, required, excluded, show_invalid, page_size, page):
        # Внимание: wf_replace_target/wf_pending_record/wf_pending_old_id — это
        # gr.State, поэтому для них возвращаются сырые значения, а не gr.update.
        return (
            [gr.update(value=msg), gr.update(visible=True),
             None, None, None]
            + _refresh_tail(sort_key, required, excluded, show_invalid, page_size, page)
            + _cls_reset()
        )

    def handle_continue(url, target, sort_key, required, excluded,
                        show_invalid, page_size, page):
        target = target or None
        rid = service.extract_id(url or "")
        if not rid:
            return _error_return(
                i18n.t("wf_err_url"), sort_key, required, excluded,
                show_invalid, page_size, page,
            )

        try:
            record = service.fetch_and_build(rid, wfpsim_url=(url or "").strip())
        except NoResultsError:
            return _error_return(
                i18n.t("wf_err_no_results"), sort_key, required, excluded,
                show_invalid, page_size, page,
            )
        except Exception as exc:  # noqa: BLE001
            return _error_return(
                i18n.t("wf_err_fetch", error=str(exc)), sort_key, required, excluded,
                show_invalid, page_size, page,
            )

        # Переносим служебные поля старой записи при замене ссылки
        if target:
            old = wdb.get(target)
            record["created_at"] = (old or {}).get("created_at", record["created_at"])
            record["not_valid"] = (old or {}).get("not_valid", False)

        unknown_items = _scan_unknowns(record)
        if unknown_items:
            # Открываем панель классификации; запись ждёт применения классификации.
            # Для gr.State возвращаем сырые значения (record, target).
            return (
                [gr.update(value=i18n.t("wf_unknown_found")), gr.update(visible=False),
                 None, record, target]
                + _refresh_tail(
                    sort_key, required, excluded, show_invalid, page_size, page
                )
                + _cls_show(unknown_items)
            )

        # Неизвестных объектов нет — добавляем/заменяем сразу.
        if target:
            wdb.delete(target)
            wdb.add_or_update(record)
            msg = i18n.t("wf_replaced")
        else:
            wdb.add_or_update(record)
            msg = i18n.t("wf_added")
        return (
            [gr.update(value=msg), gr.update(visible=False),
             None, None, None]
            + _refresh_tail(
                sort_key, required, excluded, show_invalid, page_size, page
            )
            + _cls_reset()
        )

    def handle_wf_cls_prev(page, items):
        items = items or []
        new_page = max(0, int(page or 0) - 1)
        row_u = _row_updates(wf_cls_rows, items, new_page, service.dl, cls_assign, cls_map)
        prev, nxt, label, _ = _nav_updates(items, new_page, cls_size)
        return row_u + [prev, nxt, label, new_page]

    def handle_wf_cls_next(page, items):
        items = items or []
        n_pages = _cls_n_pages(items, cls_size)
        new_page = min(int(page or 0) + 1, n_pages - 1)
        row_u = _row_updates(wf_cls_rows, items, new_page, service.dl, cls_assign, cls_map)
        prev, nxt, label, _ = _nav_updates(items, new_page, cls_size)
        return row_u + [prev, nxt, label, new_page]

    def handle_wf_cls_select(row_idx):
        def inner(value, items, page):
            items = items or []
            gi = int(page or 0) * cls_size + row_idx
            if gi < len(items):
                if value:
                    cls_map[gi] = value
                else:
                    cls_map.pop(gi, None)
            return gr.update(value=value)
        return inner

    def handle_wf_apply(*args):
        items = args[cls_size] or []
        char_map = {}
        weapon_map = {}
        for gi, (kind, name) in enumerate(items):
            val = cls_map.get(gi) or classifiers.recommended_list(kind)
            if not val:
                continue
            if kind == "char":
                char_map[name] = val
            else:
                weapon_map[name] = val

        # Записываем классификацию в wfpsim_objects.json (не в objects.json)
        classifiers.apply_classifications(wom, char_map, weapon_map)

        record = args[cls_size + 2]
        old_id = args[cls_size + 3]
        sort_key = args[cls_size + 4]
        required = args[cls_size + 5]
        excluded = args[cls_size + 6]
        show_invalid = args[cls_size + 7]
        page_size = args[cls_size + 8]
        page = args[cls_size + 9]

        # Защита от применения классификации без ожидающей записи.
        if not record:
            return (
                [gr.update(value=i18n.t(
                    "wf_err_fetch",
                    error="no pending record after classification",
                )), gr.update(visible=False), None, None, None]
                + _refresh_tail(
                    sort_key, required, excluded, show_invalid, page_size, page
                )
                + _cls_reset()
            )

        if old_id:
            wdb.delete(old_id)
            msg = i18n.t("wf_replaced")
        else:
            msg = i18n.t("wf_added")
        wdb.add_or_update(record)

        return (
            [gr.update(value=msg), gr.update(),
             None, None, None]
            + _refresh_tail(
                sort_key, required, excluded, show_invalid, page_size, page
            )
            + _cls_reset()
        )

    # --- События ---

    refresh_inputs = [
        wf_sort, wf_required, wf_excluded, wf_show_invalid, wf_page_size, wf_page,
    ]
    refresh_outputs = (
        slot_outputs
        + [wf_prev_btn, wf_next_btn, wf_page_num, wf_nav_label,
           wf_page, wf_records, wf_total_label]
    )

    # Полный набор выходов для операций с диалогом/классификацией
    full_outputs = (
        [wf_status, wf_dialog, wf_replace_target,
         wf_pending_record, wf_pending_old_id]
        + slot_outputs
        + [wf_prev_btn, wf_next_btn, wf_page_num, wf_nav_label,
           wf_page, wf_records, wf_total_label]
        + wf_cls_row_outputs
        + [wf_cls_prev_btn, wf_cls_next_btn, wf_cls_nav_label,
           wf_cls_items, wf_cls_page, wf_cls_apply_btn, wf_unknown_group]
    )

    # Изменение фильтров/сортировки сбрасывает список на первую страницу
    wf_sort.change(lambda: 1, [], [wf_page]).then(
        handle_refresh, refresh_inputs, refresh_outputs
    )
    wf_required.change(lambda: 1, [], [wf_page]).then(
        handle_refresh, refresh_inputs, refresh_outputs
    )
    wf_excluded.change(lambda: 1, [], [wf_page]).then(
        handle_refresh, refresh_inputs, refresh_outputs
    )
    wf_show_invalid.change(lambda: 1, [], [wf_page]).then(
        handle_refresh, refresh_inputs, refresh_outputs
    )
    wf_page_size.change(lambda: 1, [], [wf_page]).then(
        handle_refresh, refresh_inputs, refresh_outputs
    )

    # Пагинация: вперёд/назад и переход к странице по номеру
    wf_prev_btn.click(lambda p: max(1, int(p or 1) - 1), [wf_page], [wf_page]) \
        .then(handle_refresh, refresh_inputs, refresh_outputs)
    wf_next_btn.click(lambda p: int(p or 1) + 1, [wf_page], [wf_page]) \
        .then(handle_refresh, refresh_inputs, refresh_outputs)
    wf_page_num.change(lambda v: int(v or 1), [wf_page_num], [wf_page]) \
        .then(handle_refresh, refresh_inputs, refresh_outputs)

    dialog_open_outputs = [wf_replace_target, wf_dialog, wf_url]
    wf_add_btn.click(handle_add_open, [], dialog_open_outputs)
    wf_cancel_btn.click(handle_cancel, [], [wf_replace_target, wf_dialog])

    continue_inputs = [
        wf_url, wf_replace_target, wf_sort, wf_required, wf_excluded,
        wf_show_invalid, wf_page_size, wf_page,
    ]
    wf_continue_btn.click(handle_continue, continue_inputs, full_outputs)

    action_outputs = refresh_outputs
    action_inputs = [
        wf_sort, wf_required, wf_excluded, wf_show_invalid, wf_page_size,
        wf_page, wf_records,
    ]
    for i, slot in enumerate(slots):
        slot["delete"].click(make_action(i, "delete"), action_inputs, action_outputs)
        slot["invalid"].click(make_action(i, "invalid"), action_inputs, action_outputs)
        slot["copy"].click(
            make_copy(i), [wf_page, wf_page_size, wf_records], [wf_clipboard, wf_status]
        ).then(lambda c: c, [wf_clipboard], [wf_clipboard], js=JS_COPY_CLIPBOARD)
        slot["replace"].click(
            make_replace_open(i), [wf_page, wf_page_size, wf_records],
            dialog_open_outputs,
        )

    # Классификация
    cls_nav_outputs = wf_cls_row_outputs + [
        wf_cls_prev_btn, wf_cls_next_btn, wf_cls_nav_label, wf_cls_page,
    ]
    wf_cls_prev_btn.click(
        handle_wf_cls_prev, [wf_cls_page, wf_cls_items], cls_nav_outputs
    )
    wf_cls_next_btn.click(
        handle_wf_cls_next, [wf_cls_page, wf_cls_items], cls_nav_outputs
    )
    wf_cls_apply_btn.click(
        handle_wf_apply,
        inputs=[r["dd"] for r in wf_cls_rows]
               + [wf_cls_items, wf_cls_page, wf_pending_record, wf_pending_old_id,
                  wf_sort, wf_required, wf_excluded, wf_show_invalid,
                  wf_page_size, wf_page],
        outputs=full_outputs,
    )
    for i, r in enumerate(wf_cls_rows):
        r["dd"].change(
            handle_wf_cls_select(i),
            inputs=[r["dd"], wf_cls_items, wf_cls_page],
            outputs=[r["dd"]],
        )

    # --- Язык ---

    lang_outputs = [
        wf_add_btn, dialog_heading, wf_url, wf_continue_btn, wf_cancel_btn,
        wf_sort, wf_required, wf_excluded, wf_show_invalid, wf_page_size,
        wf_page_num, wf_prev_btn, wf_next_btn,
    ]
    for slot in slots:
        lang_outputs += [
            slot["more"], slot["replace"], slot["delete"],
            slot["invalid"], slot["copy"],
        ]
    lang_outputs += [
        wf_cls_heading, wf_cls_description, wf_cls_apply_btn,
        wf_cls_prev_btn, wf_cls_next_btn,
    ]
    for r in wf_cls_rows:
        lang_outputs.append(r["dd"])

    def update_lang(lang):
        lang = lang or "ru"
        i18n.set_lang(lang)
        updates = [
            gr.update(value=i18n.t("wf_add_btn")),
            gr.update(value=i18n.t("wf_dialog_heading")),
            gr.update(
                label=i18n.t("wf_url_label"),
                placeholder=i18n.t("wf_dialog_hint"),
            ),
            gr.update(value=i18n.t("wf_continue_btn")),
            gr.update(value=i18n.t("wf_cancel_btn")),
            gr.update(label=i18n.t("wf_sort_label"), choices=wf_sort_choices()),
            gr.update(label=i18n.t("required_label")),
            gr.update(label=i18n.t("excluded_label")),
            gr.update(label=i18n.t("wf_show_invalid")),
            gr.update(label=i18n.t("wf_page_size_label")),
            gr.update(label=i18n.t("page_label")),
            gr.update(value=i18n.t("wf_prev")),
            gr.update(value=i18n.t("wf_next")),
        ]
        for _ in slots:
            # Ссылка «Подробнее на wfpsim» обновится при последующем refresh.
            updates += [
                gr.update(),
                gr.update(value=i18n.t("wf_btn_replace")),
                gr.update(value=i18n.t("wf_btn_delete")),
                gr.update(value=i18n.t("wf_btn_invalid")),
                gr.update(value=i18n.t("wf_btn_copy")),
            ]
        updates += [
            gr.update(value=i18n.t("cls_heading")),
            gr.update(value=i18n.t("cls_description")),
            gr.update(value=i18n.t("cls_apply")),
            gr.update(value=i18n.t("cls_prev")),
            gr.update(value=i18n.t("cls_next")),
        ]
        for _ in wf_cls_rows:
            updates.append(gr.update(label=i18n.t("cls_list_label")))
        return updates

    return {
        "refresh": handle_refresh,
        "refresh_inputs": refresh_inputs,
        "refresh_outputs": refresh_outputs,
        "lang_outputs": lang_outputs,
        "update_lang": update_lang,
    }