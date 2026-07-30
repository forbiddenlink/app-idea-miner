"""
One-shot mining pipeline runner for the GitHub Actions cron.

There is no always-on worker or Redis in this setup. Celery is forced into
EAGER mode here (task_always_eager + a memory:// broker/backend) so every
task -- and any `.delay()` call a task makes internally, e.g. clustering's
`push_clusters_to_notion.delay()` -- executes inline, synchronously, in this
process. Nothing here ever opens a connection to a broker.

Usage:
    uv run python scripts/run_pipeline.py            # regular (default)
    uv run python scripts/run_pipeline.py regular     # ingestion -> processing -> clustering (+ daily alerts)
    uv run python scripts/run_pipeline.py weekly       # regular + weekly digest
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Running `python scripts/run_pipeline.py` puts scripts/ on sys.path[0], not the
# repo root, so the `apps`/`packages` workspace packages are not importable.
# Prepend the repo root (parent of scripts/) so imports resolve regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_pipeline")


def normalize_database_url_for_asyncpg() -> None:
    """
    Rewrite DATABASE_URL (if set) so the asyncpg driver can consume it.

    Neon issues connection strings like
    `postgresql://user:pass@host/db?sslmode=require&channel_binding=require`.
    asyncpg (via SQLAlchemy's async engine) does not understand `sslmode` or
    `channel_binding` as query params, so:
      - force the `postgresql+asyncpg://` scheme
      - rename `sslmode` -> `ssl` (asyncpg's equivalent connect param)
      - drop `channel_binding` entirely (unsupported, would raise on connect)

    Must run before any project module is imported: `packages.core.database`
    reads DATABASE_URL at import time to build the SQLAlchemy engine, and
    that module is pulled in transitively as soon as `apps.worker.celery_app`
    (or any task module) is imported below.
    """
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        return

    parts = urlsplit(raw)

    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"

    new_pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "channel_binding":
            continue
        if key == "sslmode":
            new_pairs.append(("ssl", value))
            continue
        new_pairs.append((key, value))

    normalized = urlunsplit(
        (scheme, parts.netloc, parts.path, urlencode(new_pairs), parts.fragment)
    )

    if normalized != raw:
        logger.info("Normalized DATABASE_URL for asyncpg (scheme/ssl params rewritten)")
    os.environ["DATABASE_URL"] = normalized


# Must happen before any apps/packages import below.
normalize_database_url_for_asyncpg()

from apps.worker.celery_app import celery_app  # noqa: E402

# One-shot cron run, not a long-lived worker: force eager execution so tasks
# (and any `.delay()`/`.apply_async()` calls they make internally) run
# in-process with no broker involved at all.
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
    broker_url="memory://",
    result_backend="cache+memory://",
)

from apps.worker.tasks.clustering import run_clustering  # noqa: E402
from apps.worker.tasks.ingestion import run_ingestion_cycle  # noqa: E402
from apps.worker.tasks.processing import process_raw_posts  # noqa: E402
from apps.worker.tasks.saved_search_alerts import (  # noqa: E402
    send_daily_saved_search_alerts,
)
from apps.worker.tasks.weekly_digest import generate_weekly_digest  # noqa: E402

# Diagnostic: confirm the effective engine URL is asyncpg-clean (no secret values).
from packages.core.database import engine as _diag_engine  # noqa: E402

logger.info(
    "effective engine: driver=%s query_keys=%s",
    _diag_engine.url.drivername,
    sorted(_diag_engine.url.query.keys()),
)


def _run_step(name: str, func) -> dict:
    logger.info("=== %s: starting ===", name)
    result = func()
    logger.info("=== %s: complete === result=%s", name, result)
    return result


def run_regular() -> None:
    """ingestion -> processing -> clustering, then daily saved-search alerts."""
    _run_step("ingestion", run_ingestion_cycle)
    _run_step("processing", process_raw_posts)
    _run_step("clustering", run_clustering)
    _run_step("saved_search_alerts_daily", send_daily_saved_search_alerts)


def run_weekly() -> None:
    """Everything in `regular`, plus the weekly idea digest."""
    run_regular()
    _run_step("weekly_digest", generate_weekly_digest)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the app-idea-miner mining pipeline once, synchronously."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="regular",
        choices=["regular", "weekly"],
        help=(
            "'regular' (ingestion -> processing -> clustering + daily alerts, "
            "default) or 'weekly' (regular + weekly digest)."
        ),
    )
    args = parser.parse_args()

    logger.info("Starting pipeline run: mode=%s", args.mode)

    try:
        if args.mode == "weekly":
            run_weekly()
        else:
            run_regular()
    except Exception:
        logger.exception("Pipeline run failed: mode=%s", args.mode)
        return 1

    logger.info("Pipeline run complete: mode=%s", args.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
