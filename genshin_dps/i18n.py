"""Интернационализация интерфейса приложения (русский / английский)."""

LANGUAGES = ("ru", "en")

_current = "ru"

# Русские надписи используются как ключи-идентификаторы переводов.
TRANSLATIONS = {
    "ru": {
        # Заголовки и вкладки
        "app_title": "Genshin Sim Statistics",
        "app_subtitle": "Таблица лидеров отрядов по урону. Данные обновляются из базы Simpact.",
        "tab_dps": "Genshin DPS Leaders",
        "tab_wfpsim": "Wfpsim database",
        # Кнопки и статусы
        "update_btn": "Обновить локальную базу",
        "status_ready": "Локальная база готова.",
        # --- Вкладка Wfpsim database ---
        "wf_heading": "### Замеры Wfpsim",
        "wf_add_btn": "Добавить новую запись",
        "wf_status_ready": "Локальная база Wfpsim готова.",
        "wf_sort_label": "Сортировка",
        "wf_sort_date": "По дате добавления",
        "wf_sort_dps": "По урону в секунду",
        "wf_link_more": "Подробнее на wfpsim",
        "wf_btn_replace": "Заменить ссылку на wfpsim",
        "wf_btn_delete": "Удалить замер",
        "wf_btn_invalid": "Изменить статус валидности",
        "wf_btn_copy": "Скопировать конфиг",
        "wf_show_invalid": "Отображать невалидные",
        "wf_page_size_label": "Записей на странице",
        "wf_dialog_heading": "Введите ссылку на запись Wfpsim",
        "wf_dialog_hint": "Формат ссылки: https://wfpsim.com/sh/{ID}",
        "wf_url_label": "Ссылка",
        "wf_continue_btn": "Продолжить",
        "wf_cancel_btn": "Отмена",
        "wf_nav": "Стр. {page} из {pages}",
        "wf_total": "Всего записей: {total}",
        "wf_empty": "Нет записей. Добавьте новую запись.",
        "wf_err_url": "Не удалось распознать ссылку. Используйте формат https://wfpsim.com/sh/{ID}",
        "wf_err_no_results": "Для этой записи в базе Wfpsim нет результатов замеров урона.",
        "wf_err_fetch": "Не удалось получить данные с Wfpsim: {error}",
        "wf_added": "Запись успешно добавлена.",
        "wf_replaced": "Ссылка записи успешно заменена.",
        "wf_copied": "Конфиг скопирован в буфер обмена.",
        "wf_deleted": "Замер удалён.",
        "wf_invalidated": "Статус валидности замера изменён.",
        "wf_prev": "◀ Назад",
        "wf_next": "Вперёд ▶",
        "wf_unknown_found": "В замере обнаружены неизвестные персонажи или оружие — "
                            "укажите список классификации для каждого объекта.",
        # Классификация неизвестных объектов
        "cls_heading": "### Классификация неизвестных объектов",
        "cls_description": "Для каждого объекта выберите список классификации из выпадающего "
                           "меню и нажмите «Применить». Для оружия показывается его изображение.",
        "cls_list_label": "Список",
        "cls_prev": "◀ Пред.",
        "cls_next": "След. ▶",
        "cls_apply": "Применить классификацию и продолжить",
        # Фильтры
        "filters_heading": "### Фильтры",
        "filter_set_label": "Набор фильтров",
        "filter_all": "Все отряды",
        "filter_kqms": "KQMS",
        "filter_kqms_selector": "KQMS с селектором",
        "filter_ftp": "FTP",
        "page_size_label": "Отрядов на странице",
        "required_label": "Обязательные персонажи (все должны быть в отряде)",
        "excluded_label": "Исключённые персонажи (ни один не должен встречаться)",
        # Отряды и пагинация
        "teams_heading": "### Отряды",
        "prev_btn": "◀ Назад",
        "page_label": "Страница",
        "next_btn": "Вперёд ▶",
        "link_more": "Подробнее на gcsim",
        "art_title": "Сет",
        "total_teams": "Всего отрядов: {total} · страница {page} из {pages}",
        "no_teams": "Нет отрядов, соответствующих фильтрам.",
        "total_label": "Всего отрядов: {total}",
        "nav_page": "Стр. {page} из {pages}",
        # Сообщения обработчиков
        "update_started": "Начинаем обновление локальной базы из Simpact...",
        "update_done": "Обновление завершено: выгружено {fetched}, в базу добавлено/обновлено "
                       "{merged}, пропущено {skipped}. Всего в базе: {total}.",
        "fetched_unknown": "Выгружено {total} записей. Обнаружены неизвестные объекты — укажите "
                           "список классификации для каждого и нажмите «Применить».",
        # Сообщения прогресса
        "progress_fetch": "Выгрузка страницы skip={skip}...",
        "progress_filter": "Фильтрация и обновление локальной базы...",
        "progress_download": "Скачивание изображений...",
        # Язык
        "language_label": "Язык",
    },
    "en": {
        "app_title": "Genshin Sim Statistics",
        "app_subtitle": "Leaderboard of teams by damage. Data is updated from the Simpact database.",
        "tab_dps": "Genshin DPS Leaders",
        "tab_wfpsim": "Wfpsim database",
        "update_btn": "Update local database",
        "status_ready": "Local database is ready.",
        # --- Wfpsim database tab ---
        "wf_heading": "### Wfpsim measurements",
        "wf_add_btn": "Add new record",
        "wf_status_ready": "Local Wfpsim database is ready.",
        "wf_sort_label": "Sort by",
        "wf_sort_date": "By added date",
        "wf_sort_dps": "By damage per second",
        "wf_link_more": "Details on wfpsim",
        "wf_btn_replace": "Replace wfpsim link",
        "wf_btn_delete": "Delete measurement",
        "wf_btn_invalid": "Toggle validity status",
        "wf_btn_copy": "Copy config",
        "wf_show_invalid": "Show invalid",
        "wf_page_size_label": "Records per page",
        "wf_dialog_heading": "Enter a Wfpsim record link",
        "wf_dialog_hint": "Link format: https://wfpsim.com/sh/{ID}",
        "wf_url_label": "Link",
        "wf_continue_btn": "Continue",
        "wf_cancel_btn": "Cancel",
        "wf_nav": "Page {page} of {pages}",
        "wf_total": "Total records: {total}",
        "wf_empty": "No records. Add a new record.",
        "wf_err_url": "Could not recognize the link. Use the format https://wfpsim.com/sh/{ID}",
        "wf_err_no_results": "This record has no damage measurement results in the Wfpsim database.",
        "wf_err_fetch": "Could not fetch data from Wfpsim: {error}",
        "wf_added": "Record added successfully.",
        "wf_replaced": "Record link replaced successfully.",
        "wf_copied": "Config copied to clipboard.",
        "wf_deleted": "Measurement deleted.",
        "wf_invalidated": "Measurement validity status changed.",
        "wf_prev": "◀ Back",
        "wf_next": "Forward ▶",
        "wf_unknown_found": "The measurement contains unknown characters or weapons — "
                            "select a classification list for each object.",
        "cls_heading": "### Classify unknown objects",
        "cls_description": "For each object, select a classification list from the dropdown menu "
                           "and press “Apply”. For weapons, the image is shown.",
        "cls_list_label": "List",
        "cls_prev": "◀ Prev",
        "cls_next": "Next ▶",
        "cls_apply": "Apply classification and continue",
        "filters_heading": "### Filters",
        "filter_set_label": "Filter set",
        "filter_all": "All teams",
        "filter_kqms": "KQMS",
        "filter_kqms_selector": "KQMS with selector",
        "filter_ftp": "FTP",
        "page_size_label": "Teams per page",
        "required_label": "Required characters (all must be in the team)",
        "excluded_label": "Excluded characters (none may appear)",
        "teams_heading": "### Teams",
        "prev_btn": "◀ Back",
        "page_label": "Page",
        "next_btn": "Forward ▶",
        "link_more": "Details on gcsim",
        "art_title": "Set",
        "total_teams": "Total teams: {total} · page {page} of {pages}",
        "no_teams": "No teams matching the filters.",
        "total_label": "Total teams: {total}",
        "nav_page": "Page {page} of {pages}",
        "update_started": "Starting local database update from Simpact...",
        "update_done": "Update finished: {fetched} fetched, {merged} added/updated in the database, "
                       "{skipped} skipped. Total in database: {total}.",
        "fetched_unknown": "{total} records fetched. Unknown objects found — select a "
                           "classification list for each and press “Apply”.",
        "progress_fetch": "Fetching page skip={skip}...",
        "progress_filter": "Filtering and updating the local database...",
        "progress_download": "Downloading images...",
        "language_label": "Language",
    },
}

LANG_LABELS = {
    "ru": "Русский",
    "en": "English",
}


def get_lang() -> str:
    """Возвращает текущий язык интерфейса."""
    return _current


def set_lang(lang: str) -> None:
    """Устанавливает текущий язык интерфейса, если он разрешён."""
    global _current
    if lang in LANGUAGES:
        _current = lang


def t(key: str, **kwargs) -> str:
    """
    Возвращает строку для текущего языка по ключу-переводу.

    Если ключ не найден или перевода нет, возвращается русский вариант.
    """
    table = TRANSLATIONS.get(_current, TRANSLATIONS["ru"])
    text = table.get(key)
    if text is None:
        text = TRANSLATIONS["ru"].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text