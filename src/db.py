from __future__ import annotations

import json
import psycopg
from dataclasses import dataclass
import logging
from typing import Any, Dict


@dataclass
class Database:
    conn: psycopg.Connection

    @classmethod
    def open(cls, database_url: str) -> "Database":
        log = logging.getLogger(__name__)
        conn = psycopg.connect(database_url)
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

