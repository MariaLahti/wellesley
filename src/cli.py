from __future__ import annotations

import argparse
import json
import logging
from typing import List

from .config import load_config
from .db import Database
from .http_client import HttpClient
from .scraper import Scraper


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="通用活动抓取 CLI")
    sub = p.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="定时抓取两个列表所有页并抓取详情，仅入库详情")
    p_run.add_argument("--interval-minutes", type=int, help="间隔分钟，默认取环境变量")
    p_run.add_argument("--max-pages", type=int, help="最多抓取页数（可选，用于限制）")
    p_run.add_argument("--domestic-id", help="境内分类ID（覆盖环境变量）")
    p_run.add_argument("--overseas-id", help="境外分类ID（覆盖环境变量）")

    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    cfg = load_config()
    db = Database.open(cfg.database_url)
    http = HttpClient(cfg)
    scraper = Scraper(cfg, db, http)

    if args.command == "run":
        import time
        logging.getLogger(__name__).info("scheduler_started")
        interval = args.interval_minutes or cfg.schedule_interval_minutes
        domestic_id = args.domestic_id or (cfg.domestic_category_id or "")
        overseas_id = args.overseas_id or (cfg.overseas_category_id or "")
        max_pages = args.max_pages or cfg.max_pages
        if not domestic_id or not overseas_id:
            raise SystemExit("DOMESTIC_CATEGORY_ID 与 OVERSEAS_CATEGORY_ID 需配置或通过参数传入")
        while True:
            logging.getLogger(__name__).info("tick_start interval_min=%s", interval)
            scraper.scrape_all_pages_and_details(domestic_id, overseas_id, max_pages=max_pages)
            logging.getLogger(__name__).info("tick_end sleeping_min=%s", interval)
            time.sleep(max(1, int(interval)) * 60)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

