"""Сборка исполняемого файла (.exe) сервиса Genshin Sim Statistics.

Использует PyInstaller в режиме onefile (консольный вариант, чтобы uvicorn/gradio
могли писать логи и корректно настраивать форматтеры). После сборки:
  - итоговый ``GenshinSimStatistics.exe`` кладётся в корневую папку репозитория;
  - данные, необходимые для запуска (objects.json, README.md, LICENSE),
    находятся в корне рядом с .exe;
  - служебные артефакты сборки (папки build/ и dist/, файл *.spec) удаляются.

Запуск:
    python build.py
    # или на Windows:
    build.bat
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

APP_NAME = "GenshinSimStatistics"

# Данные, которые должны лежать рядом с исполняемым файлом при запуске.
# objects.json хранится в cache/; перед сборкой его копия размещается рядом с .exe,
# чтобы при первом запуске приложение заполнило cache/objects.json (см. config).
RUNTIME_DATA = ["objects.json", "README.md", "LICENSE"]

# Источник классификационных списков для копирования рядом с .exe.
OBJECTS_SOURCE = ROOT / "cache" / "objects.json"

# Служебные папки PyInstaller
WORK_DIR = ROOT / "build"
LEGACY_DIST_DIR = ROOT / "dist"


def _ensure_pyinstaller() -> None:
    """Устанавливает PyInstaller, если он не установлен."""
    try:
        import PyInstaller  # noqa: F401
        print("[build] PyInstaller найден")
    except ImportError:
        print("[build] PyInstaller не установлен, устанавливаю...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=True,
        )


def _clean_previous() -> None:
    """Удаляет предыдущие результаты сборки (exe, build/, dist/, *.spec)."""
    exe = ROOT / f"{APP_NAME}.exe"
    if exe.exists():
        print(f"[build] Удаляю предыдущий exe: {exe}")
        exe.unlink()
    for path in (WORK_DIR, LEGACY_DIST_DIR):
        if path.exists():
            print(f"[build] Удаляю папку: {path}")
            shutil.rmtree(path, ignore_errors=True)
    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        print(f"[build] Удаляю предыдущий spec: {spec}")
        spec.unlink()


def _run_pyinstaller() -> None:
    """Запускает PyInstaller для сборки onefile-исполняемого файла."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name", APP_NAME,
        "--distpath", str(ROOT),      # exe в корневую папку репозитория
        "--workpath", str(WORK_DIR),  # временная рабочая папка build/
        "--specpath", str(ROOT),      # временный файл *.spec в корне
        # Gradio и gradio_client поставляют фронтенд и JSON-данные (types.json и т.п.),
        # которые обязательно должны попасть в сборку.
        "--collect-all", "gradio",
        "--collect-all", "gradio_client",
        "--copy-metadata", "gradio",
        "--copy-metadata", "gradio_client",
        str(ROOT / "app.py"),
    ]
    print(f"[build] Запуск PyInstaller: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def _ensure_runtime_data() -> None:
    """Гарантирует наличие данных для запуска рядом с .exe в корне."""
    # objects.json перенесён в cache/; для .exe создаём его копию в корне,
    # чтобы приложение при первом запуске заполнило cache/objects.json.
    objects_dest = ROOT / "objects.json"
    if OBJECTS_SOURCE.exists():
        if not objects_dest.exists() or OBJECTS_SOURCE.stat().st_mtime > objects_dest.stat().st_mtime:
            print(f"[build] Копирую objects.json из {OBJECTS_SOURCE}")
            import shutil
            shutil.copy2(OBJECTS_SOURCE, objects_dest)
    for name in RUNTIME_DATA:
        src = ROOT / name
        if src.exists():
            print(f"[build] Данные рядом с exe: {src}")
        else:
            print(f"[build] Предупреждение: не найден файл данных {name}")


def _cleanup_artifacts() -> None:
    """Удаляет служебные артефакты сборки (build/, dist/, *.spec)."""
    for path in (WORK_DIR, LEGACY_DIST_DIR):
        if path.exists():
            print(f"[build] Удаляю служебную папку: {path}")
            shutil.rmtree(path, ignore_errors=True)
    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        print(f"[build] Удаляю файл спецификации: {spec}")
        spec.unlink()


def main() -> None:
    """Выполняет полный цикл сборки."""
    _ensure_pyinstaller()
    _clean_previous()
    _run_pyinstaller()
    _ensure_runtime_data()
    _cleanup_artifacts()

    exe = ROOT / f"{APP_NAME}.exe"
    if exe.exists():
        print("\n[build] Сборка успешно завершена!")
        print(f"[build] Исполняемый файл: {exe}")
    else:
        print("\n[build] ОШИБКА: исполняемый файл не найден после сборки.")
        sys.exit(1)


if __name__ == "__main__":
    main()