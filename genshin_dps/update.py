"""Оркестрация полного обновления локальной базы из Simpact."""

from . import classifiers, downloader, filters, i18n, models


def fetch_phase(dl, om, progress=None):
    """
    Выгружает все записи из Simpact и собирает неизвестные объекты.
    Возвращает (raw_records, collector, total_fetched).
    """
    raw = []
    collector = classifiers.UnknownCollector(om)

    def on_page(data, skip):
        if progress is not None:
            # Количество страниц заранее неизвестно — используем неопределённый
            # индикатор прогресса (индекс + None для общего числа шагов).
            progress((1, None), i18n.t("progress_fetch", skip=skip))
        for rec in data:
            collector.scan_record(rec)
            raw.append(rec)

    total = dl.fetch_all(on_page=on_page)
    return raw, collector, total


def finalize_phase(raw, om, ldb, dl, char_map=None, weapon_map=None,
                   force_assets=False, progress=None):
    """
    Применяет классификации, фильтрует записи, обновляет локальную базу
    и скачивает изображения. Возвращает статистику.
    """
    classifiers.apply_classifications(om, char_map or {}, weapon_map or {})

    merged = 0
    skipped = 0
    n = max(len(raw), 1)
    for i, rec in enumerate(raw):
        if progress is not None:
            progress(i / n, i18n.t("progress_filter"))
        if filters.is_allowed(rec, om):
            record = models.team_to_record(rec)
            record["flags"] = filters.compute_flags(record["team"], om)
            ldb.merge(record)
            merged += 1
        else:
            skipped += 1
    ldb.save()

    total_records = len(ldb.records)
    m = max(total_records, 1)
    for i, rec in enumerate(ldb.records):
        if progress is not None:
            progress(i / m, i18n.t("progress_download"))
        downloader.download_record_assets(dl, rec, force=force_assets)

    return {
        "total_fetched": len(raw),
        "merged": merged,
        "skipped": skipped,
        "total_in_db": total_records,
    }


def full_update(om, ldb, dl, unknown_callback=None, force_assets=False, progress=None):
    """
    Полный цикл обновления. При обнаружении неизвестных объектов вызывается
    unknown_callback(collector), который должен вернуть (char_map, weapon_map).
    """
    raw, collector, _ = fetch_phase(dl, om, progress)
    if not collector.is_empty():
        if unknown_callback is None:
            raise RuntimeError(
                "Обнаружены неизвестные персонажи/оружие; требуется классификация."
            )
        char_map, weapon_map = unknown_callback(collector)
    else:
        char_map, weapon_map = {}, {}
    return finalize_phase(raw, om, ldb, dl, char_map, weapon_map, force_assets, progress)