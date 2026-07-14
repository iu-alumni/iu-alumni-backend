#!/usr/bin/env python3
"""Compute Local Legend winners for a target year.

By default runs for the previous calendar year (the cron use case).
Pass `--year YYYY` for a backfill.

Usage:
    python scripts/recompute_local_legend.py
    python scripts/recompute_local_legend.py --year 2024
"""

import argparse
from datetime import datetime
import logging
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.badges import compute_local_legend_winners


load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("local_legend_cron")


def _session():
    url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not url:
        raise RuntimeError("SQLALCHEMY_DATABASE_URL not set")
    engine = create_engine(url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Calendar year to compute winners for (defaults to previous year)",
    )
    args = parser.parse_args()

    target_year = (
        args.year if args.year is not None else datetime.utcnow().year - 1
    )
    logger.info("Computing Local Legend winners for year %s", target_year)

    db = _session()
    try:
        winners = compute_local_legend_winners(db, target_year)
        logger.info(
            "Local Legend %s complete: %d winners awarded", target_year, len(winners)
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
