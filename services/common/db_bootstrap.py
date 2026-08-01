"""DB schema / seed without blocking uvicorn listen (K8s probes)."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

log = logging.getLogger("noli.db")


def init_db_in_background(
    *,
    label: str,
    create_schema: Callable[[], None],
    seed: Callable[[], None] | None = None,
    attempts: int = 60,
    delay_seconds: float = 2.0,
) -> None:
    """Run create_all (+ optional seed) in a daemon thread with retries.

    FastAPI lifespan blocks accepting connections until it yields. Doing DB
    work inline causes readiness/liveness connection-refused → CrashLoop (137).
    """

    def _run() -> None:
        for i in range(1, attempts + 1):
            try:
                create_schema()
                if seed is not None:
                    seed()
                log.info("[%s] database ready (attempt %s)", label, i)
                print(f"[{label}] database ready (attempt {i})", flush=True)
                return
            except Exception as exc:  # noqa: BLE001 — retry until Postgres up
                msg = f"[{label}] db init attempt {i}/{attempts}: {exc}"
                log.warning(msg)
                print(msg, flush=True)
                time.sleep(delay_seconds)
        print(f"[{label}] database init FAILED after {attempts} attempts", flush=True)

    threading.Thread(target=_run, name=f"{label}-db-init", daemon=True).start()
