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
        log = logging.getLogger(__name__)
        with self.conn.cursor() as cur:
            # 检查表是否已存在
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'activity_detail'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                log.info("Creating activity_detail table as it doesn't exist")
                cur.execute(
                    """
                    CREATE TABLE activity_detail (
                        id SERIAL PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        type TEXT NOT NULL,
                        date_key TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        activity_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(activity_id, date_key, platform)
                    );
                    """
                )
                self.conn.commit()
                log.info("activity_detail table created successfully")
            else:
                log.info("activity_detail table already exists, skipping creation")

    def save_activity_detail(self, activity_id: str, date_key: str, activity_data: Dict[str, Any], type_text: str, platform: str) -> None:
        logging.getLogger(__name__).info(
            "db_upsert_detail activity_id=%s date_key=%s platform=%s", activity_id, date_key, platform
        )
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO activity_detail (activity_id, type, date_key, platform, activity_data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (activity_id, date_key, platform) DO UPDATE SET
                    activity_data = EXCLUDED.activity_data
                """,
                (activity_id, type_text, date_key, platform, json.dumps(activity_data, ensure_ascii=False)),
            )
            self.conn.commit()


__all__ = ["Database"]

