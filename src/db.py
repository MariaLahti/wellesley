from __future__ import annotations

import json
import psycopg
from dataclasses import dataclass
import logging
import time
from typing import Any, Dict


@dataclass
class Database:
    conn: psycopg.Connection

    @classmethod
    def open(cls, database_url: str) -> "Database":
        log = logging.getLogger(__name__)
        # 简单重试以应对容器启动时数据库尚未就绪
        last_err: Exception | None = None
        for attempt in range(1, 16):  # ~30s（1,2,2,3,3...）
            try:
                conn = psycopg.connect(database_url)
                break
            except Exception as e:
                last_err = e
                sleep_s = 2 if attempt > 1 else 1
                log.warning("db_connect_retry attempt=%s sleep=%ss", attempt, sleep_s)
                time.sleep(sleep_s)
        else:
            # 用最后一次异常抛出
            raise last_err  # type: ignore[misc]
        db = cls(conn)
        db._init_schema()
        log.info("db_open")
        return db

    def _init_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS activity_detail;")
            cur.execute(
                """
                CREATE TABLE activity_detail (
                    id SERIAL PRIMARY KEY,
                    activity_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    date_key TEXT NOT NULL,
                    activity_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(activity_id, date_key)
                );
                """
            )
            self.conn.commit()

    def save_activity_detail(self, activity_id: str, date_key: str, activity_data: Dict[str, Any], type_text: str) -> None:
        logging.getLogger(__name__).info(
            "db_upsert_detail activity_id=%s date_key=%s", activity_id, date_key
        )
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO activity_detail (activity_id, type, date_key, activity_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (activity_id, date_key) DO UPDATE SET
                    activity_data = EXCLUDED.activity_data
                """,
                (activity_id, type_text, date_key, json.dumps(activity_data, ensure_ascii=False)),
            )
            self.conn.commit()


__all__ = ["Database"]

