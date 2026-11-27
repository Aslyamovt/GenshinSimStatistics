"""Точка входа приложения Genshin Sim Statistics."""

import os
import time

from genshin_dps import config
from genshin_dps.ui import build_demo


def _allow_localhost_direct() -> None:
    """Исключает локальные адреса из прокси.

    Gradio при запуске проверяет доступность собственного локального адреса
    через httpx. Если в системе заданы HTTP_PROXY/HTTPS_PROXY без localhost в
    NO_PROXY, проверка уходит на прокси и завершается ошибкой
    «When localhost is not accessible...». Добавляем локальные адреса в
    NO_PROXY, чтобы проверка шла напрямую.
    """
    hosts = ("localhost", "127.0.0.1", "::1")
    for var in ("NO_PROXY", "no_proxy"):
        current = os.environ.get(var, "")
        items = [item.strip() for item in current.split(",") if item.strip()]
        lowered = {item.lower() for item in items}
        for host in hosts:
            if host.lower() not in lowered:
                items.append(host)
                lowered.add(host.lower())
        os.environ[var] = ",".join(items)


def _patch_gradio_local_check() -> None:
    """Делает проверку локального адреса Gradio устойчивой к медленному старту.

    Gradio сразу после запуска сервера проверяет доступность собственного
    локального URL. На Windows сервер может подниматься на 1–2 секунды дольше,
    и стандартная проверка (5 попыток) успевает завершиться ошибкой
    «When localhost is not accessible...». Заменяем её на более терпеливую:
    ждём до 30 секунд.
    """
    try:
        import httpx
        import gradio.networking as networking
    except Exception:  # noqa: BLE001
        return

    def patient_url_ok(url: str) -> bool:
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                response = httpx.head(url, timeout=2, verify=False)
                if response.status_code in (200, 401, 302):
                    return True
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.5)
        return False

    networking.url_ok = patient_url_ok


def main():
    _allow_localhost_direct()
    _patch_gradio_local_check()
    config.ensure_cache_dirs()
    demo = build_demo()
    # Явно привязываемся к IPv4-loopback: это исключает проблемы, когда
    # localhost резолвится в ::1, а сервер слушает 127.0.0.1.
    demo.launch(server_name="127.0.0.1")


if __name__ == "__main__":
    main()