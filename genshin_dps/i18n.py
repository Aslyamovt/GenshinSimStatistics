"""Интернационализация интерфейса приложения (русский / английский)."""

LANGUAGES = ("ru", "en")

_current = "ru"

# Русские надписи используются как ключи-идентификаторы переводов.
TRANSLATIONS = {
    "ru": {
        # Заголовки и описание
        "app_title": "Genshin DPS leaders",
        "app_subtitle": "Таблица лидеров отрядов по урону. Данные обновляются из базы Simpact.",
        # Кнопки и статусы
        "update_btn": "Обновить локальную базу",
        "status_ready": "Локальная база готова.",
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
        "app_title": "Genshin DPS leaders",
        "app_subtitle": "Leaderboard of teams by damage. Data is updated from the Simpact database.",
        "update_btn": "Update local database",
        "status_ready": "Local database is ready.",
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