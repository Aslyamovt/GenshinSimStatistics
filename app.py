"""Точка входа приложения Genshin DPS leaders."""

from genshin_dps import config
from genshin_dps.ui import build_demo


def main():
    config.ensure_cache_dirs()
    demo = build_demo()
    demo.launch()


if __name__ == "__main__":
    main()