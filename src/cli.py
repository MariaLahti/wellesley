from __future__ import annotations

import argparse
import json
import logging
from typing import List

from .db import Database
from .platforms.common.config import BaseConfig
from .platforms.tiga.config import TigaConfig
from .platforms.tiga.http_client import TigaHttpClient
from .platforms.tiga.scraper import TigaScraper
from .platforms.gaia.config import GaiaConfig
from .platforms.gaia.http_client import GaiaHttpClient
from .platforms.gaia.scraper import GaiaScraper


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="通用活动抓取 CLI")
    sub = p.add_subparsers(dest="command", required=True)

    p_tiga = sub.add_parser("tiga", help="抓取 Tiga 平台活动数据")
    p_tiga.add_argument("--interval-minutes", type=int, help="间隔分钟，默认取环境变量")
    p_tiga.add_argument("--max-pages", type=int, help="最多抓取页数（可选，用于限制）")

    p_gaia = sub.add_parser("gaia", help="抓取 Gaia 平台活动数据（详情+团期）")
    p_gaia.add_argument("--catalogs", nargs="+", help="分类列表，默认从环境变量读取")
    p_gaia.add_argument("--max-pages", type=int, help="每个分类最大抓取页数（可选）")
    p_gaia.add_argument("--interval-minutes", type=int, help="定时运行间隔分钟数（可选，不指定则仅运行一次）")

    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    
    base_config = BaseConfig.from_env()
    db = Database.open(base_config.database_url)

    if args.command == "tiga":
        import time
        tiga_config = TigaConfig()
        tiga_http = TigaHttpClient(base_config, tiga_config)
        tiga_scraper = TigaScraper(db, tiga_http, tiga_config)
        
        interval = args.interval_minutes or tiga_config.schedule_interval_minutes
        max_pages = args.max_pages or tiga_config.max_pages
        
        logging.getLogger(__name__).info("tiga_scheduler_started interval_min=%s", interval)
        while True:
            logging.getLogger(__name__).info("tiga_tick_start")
            tiga_scraper.scrape_activities(max_pages=max_pages)
            logging.getLogger(__name__).info("tiga_tick_end sleeping_min=%s", interval)
            time.sleep(max(1, int(interval)) * 60)
        return 0
    
    elif args.command == "gaia":
        import time
        gaia_config = GaiaConfig()
        gaia_http = GaiaHttpClient(base_config, gaia_config)
        gaia_scraper = GaiaScraper(db, gaia_http, gaia_config)
        
        if args.catalogs:
            gaia_config.catalogs = args.catalogs
        max_pages = args.max_pages or gaia_config.max_pages
        interval = args.interval_minutes
        
        if interval:
            logging.getLogger(__name__).info("gaia_scheduler_started catalogs=%s interval_min=%s", gaia_config.catalogs, interval)
            while True:
                logging.getLogger(__name__).info("gaia_tick_start")
                gaia_scraper.scrape_activities(max_pages=max_pages)
                logging.getLogger(__name__).info("gaia_tick_end sleeping_min=%s", interval)
                time.sleep(max(1, int(interval)) * 60)
        else:
            logging.getLogger(__name__).info("gaia_single_run catalogs=%s", gaia_config.catalogs)
            gaia_scraper.scrape_activities(max_pages=max_pages)
        return 0
    
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

