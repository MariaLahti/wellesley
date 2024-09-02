from __future__ import annotations

from typing import Any, Dict, List
import logging

from flask import Flask, request, render_template, redirect, url_for, session
import psycopg

from .platforms.common.config import BaseConfig


app = Flask(__name__)
log = logging.getLogger(__name__)


def pg_connect():
    cfg = BaseConfig.from_env()
    app.config.setdefault('SECRET_KEY', cfg.secret_key)
    return psycopg.connect(cfg.database_url)


def query_with_param(params: Dict[str, str], key: str, value: str) -> str:
    new_params = params.copy()
    new_params[key] = value
    return "&".join(f"{k}={v}" for k, v in new_params.items())


@app.template_global()
def query_with(key: str, value: str) -> str:
    return query_with_param(dict(request.args.items()), key, value)


def _require_login():
    cfg = BaseConfig.from_env()
    if not cfg.web_username or not cfg.web_password:
        return True
    return session.get("authed") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    cfg = BaseConfig.from_env()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if cfg.web_username and cfg.web_password and username == cfg.web_username and password == cfg.web_password:
            session["authed"] = True
            return redirect(url_for("platform_select"))
        return render_template("login.html", error="账号或密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def platform_select():
    if not _require_login():
        return redirect(url_for("login"))
    cfg = BaseConfig.from_env()
    return render_template("platform_select.html",
                         tiga_display_name=cfg.tiga_display_name,
                         gaia_display_name=cfg.gaia_display_name)


@app.route("/tiga")
def tiga_dashboard():
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "collect_count")
    order = request.args.get("order", "desc")
    date_key = request.args.get("date", _date.today().isoformat())
    type_filter = request.args.get("type", "all")
    order_sql = "DESC" if order != "asc" else "ASC"

    # 排序字段映射到 JSON 路径
    sort_map = {
        "collect_count": "COALESCE(NULLIF(activity_data->>'collect_count','')::numeric,0)",
        "total_comment.count": "COALESCE(NULLIF(activity_data->'total_comment'->>'count','')::numeric,0)",
        "total_comment.average": "NULLIF(activity_data->'total_comment'->>'average','')::numeric",
        "activityType.one_week_uv": "COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'one_week_uv','')::numeric,0)",
        "activityType.two_month_uv": "COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'two_month_uv','')::numeric,0)",
        "activityType.history_signup_count": "COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'history_signup_count','')::numeric,0)",
    }

    sort_sql = sort_map.get(sort, sort_map["collect_count"]) + f" {order_sql} NULLS LAST"

    where_sql = "WHERE date_key = %s AND platform = %s"
    params: List[Any] = [date_key, "tiga"]
    if q:
        where_sql += " AND activity_data->>'title' ILIKE %s"
        params.append(f"%{q}%")
    if type_filter in ("domestic", "overseas"):
        where_sql += " AND type = %s"
        params.append(type_filter)

    sql = f"""
        SELECT activity_id,
               date_key,
               platform,
               activity_data->>'title'               AS title,
               COALESCE(NULLIF(activity_data->>'collect_count','')::int, 0) AS collect_count,
               COALESCE(NULLIF(activity_data->'total_comment'->>'count','')::int, 0) AS total_comment_count,
               NULLIF(activity_data->'total_comment'->>'average','')::numeric AS total_comment_average,
               COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'one_week_uv','')::int, 0) AS one_week_uv,
               COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'two_month_uv','')::int, 0) AS two_month_uv,
               COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'history_signup_count','')::int, 0) AS history_signup_count
        FROM activity_detail
        {where_sql}
        ORDER BY {sort_sql}
        LIMIT 200
    """

    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [
                {
                    "activity_id": r[0],
                    "date_key": r[1],
                    "platform": r[2],
                    "title": r[3] or "",
                    "collect_count": r[4] or 0,
                    "total_comment_count": r[5] or 0,
                    "total_comment_average": float(r[6]) if r[6] is not None else None,
                    "one_week_uv": r[7] or 0,
                    "two_month_uv": r[8] or 0,
                    "history_signup_count": r[9] or 0,
                }
                for r in cur.fetchall()
            ]

    cfg = BaseConfig.from_env()
    return render_template(
        "tiga_dashboard.html",
        rows=rows,
        q=q,
        sort=sort,
        order=order,
        date_key=date_key,
        type_filter=type_filter,
        tiga_display_name=cfg.tiga_display_name,
        sort_options={
            "collect_count": "收藏人数",
            "total_comment.count": "评论人数",
            "total_comment.average": "评论平均分",
            "activityType.one_week_uv": "活动周访客数",
            "activityType.two_month_uv": "活动月访客数",
            "activityType.history_signup_count": "历史报名人数",
        },
    )


@app.route("/gaia")
def gaia_dashboard():
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "detail.minPrice")
    order = request.args.get("order", "desc")
    date_key = request.args.get("date", _date.today().isoformat())
    catalog_filter = request.args.get("catalog", "all")
    order_sql = "DESC" if order != "asc" else "ASC"

    # Gaia 平台的排序字段映射
    sort_map = {
        "detail.minPrice": "COALESCE(NULLIF(activity_data->'detail'->>'minPrice','')::numeric,0)",
        "detail.maxPrice": "COALESCE(NULLIF(activity_data->'detail'->>'maxPrice','')::numeric,0)",
        "detail.minSize": "COALESCE(NULLIF(activity_data->'detail'->>'minSize','')::numeric,0)",
        "detail.maxSize": "COALESCE(NULLIF(activity_data->'detail'->>'maxSize','')::numeric,0)",
        "times.count": "COALESCE(jsonb_array_length(activity_data->'times'), 0)",
    }

    sort_sql = sort_map.get(sort, sort_map["detail.minPrice"]) + f" {order_sql} NULLS LAST"

    where_sql = "WHERE date_key = %s AND platform = %s"
    params: List[Any] = [date_key, "gaia"]
    if q:
        where_sql += " AND activity_data->'detail'->>'heading' ILIKE %s"
        params.append(f"%{q}%")
    if catalog_filter != "all":
        where_sql += " AND type = %s"
        params.append(catalog_filter)

    # Gaia 分类名称映射
    catalog_names = {
        "E": "国际旅行", "L": "长途旅行", "SW": "超级周末",
        "S": "短途旅行", "WE": "城市活动", "SY": "青春系列"
    }

    sql = f"""
        SELECT activity_id,
               date_key,
               platform,
               type,
               activity_data->'detail'->>'heading' AS title,
               COALESCE(NULLIF(activity_data->'detail'->>'minPrice','')::numeric, 0) AS min_price,
               COALESCE(NULLIF(activity_data->'detail'->>'maxPrice','')::numeric, 0) AS max_price,
               COALESCE(NULLIF(activity_data->'detail'->>'minSize','')::int, 0) AS min_size,
               COALESCE(NULLIF(activity_data->'detail'->>'maxSize','')::int, 0) AS max_size,
               COALESCE(NULLIF(activity_data->'detail'->>'surplusSize','')::int, 0) AS surplus_size,
               COALESCE(jsonb_array_length(activity_data->'times'), 0) AS times_count
        FROM activity_detail
        {where_sql}
        ORDER BY {sort_sql}
        LIMIT 200
    """

    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [
                {
                    "activity_id": r[0],
                    "date_key": r[1],
                    "platform": r[2],
                    "catalog": r[3],
                    "catalog_name": catalog_names.get(r[3], r[3]),
                    "title": r[4] or "",
                    "min_price": float(r[5]) if r[5] is not None else 0,
                    "max_price": float(r[6]) if r[6] is not None else 0,
                    "min_size": r[7] or 0,
                    "max_size": r[8] or 0,
                    "surplus_size": r[9] or 0,
                    "times_count": r[10] or 0,
                }
                for r in cur.fetchall()
            ]

    cfg = BaseConfig.from_env()
    return render_template(
        "gaia_dashboard.html",
        rows=rows,
        q=q,
        sort=sort,
        order=order,
        date_key=date_key,
        catalog_filter=catalog_filter,
        gaia_display_name=cfg.gaia_display_name,
        sort_options={
            "detail.minPrice": "最低价格",
            "detail.maxPrice": "最高价格",
            "detail.minSize": "最小人数",
            "detail.maxSize": "最大人数",
            "times.count": "团期数量",
        },
    )


@app.route("/gaia/trends")
def gaia_trends():
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date, timedelta

    # 默认日期范围为过去7天
    end_date = _date.today()
    start_date = end_date - timedelta(days=6)

    start_date_str = request.args.get("start_date", start_date.isoformat())
    end_date_str = request.args.get("end_date", end_date.isoformat())
    activity_id = request.args.get("activity_id", "").strip()
    dimensions = request.args.getlist("dimensions") or [
        "detail.minPrice", "detail.maxPrice", "detail.minSize", "detail.maxSize", "detail.surplusSize", "times.count"
    ]

    where_sql = "WHERE date_key >= %s AND date_key <= %s AND platform = %s"
    params = [start_date_str, end_date_str, "gaia"]

    if activity_id:
        where_sql += " AND activity_id = %s"
        params.append(activity_id)

    sql = f"""
        SELECT activity_id,
               activity_data->'detail'->>'heading' AS title,
               date_key,
               COALESCE(NULLIF(activity_data->'detail'->>'minPrice','')::numeric, 0) AS min_price,
               COALESCE(NULLIF(activity_data->'detail'->>'maxPrice','')::numeric, 0) AS max_price,
               COALESCE(NULLIF(activity_data->'detail'->>'minSize','')::int, 0) AS min_size,
               COALESCE(NULLIF(activity_data->'detail'->>'maxSize','')::int, 0) AS max_size,
               COALESCE(NULLIF(activity_data->'detail'->>'surplusSize','')::int, 0) AS surplus_size,
               COALESCE(jsonb_array_length(activity_data->'times'), 0) AS times_count
        FROM activity_detail
        {where_sql}
        ORDER BY activity_id, date_key
    """

    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [
                {
                    "activity_id": r[0],
                    "title": r[1] or "",
                    "date_key": r[2],
                    "min_price": float(r[3]) if r[3] is not None else 0,
                    "max_price": float(r[4]) if r[4] is not None else 0,
                    "min_size": r[5] or 0,
                    "max_size": r[6] or 0,
                    "surplus_size": r[7] or 0,
                    "times_count": r[8] or 0,
                }
                for r in cur.fetchall()
            ]

    # 组织数据按activity_id分组
    trend_data = {}
    for row in rows:
        aid = row["activity_id"]
        if aid not in trend_data:
            trend_data[aid] = {
                "title": row["title"],
                "activity_id": aid,
                "dates": [],
                "data": {dim: [] for dim in dimensions}
            }

        trend_data[aid]["dates"].append(row["date_key"])
        for dim in dimensions:
            key = dim.replace("detail.", "").replace("times.", "times_")
            trend_data[aid]["data"][dim].append(row.get(key, 0))

    cfg = BaseConfig.from_env()
    return render_template(
        "gaia_trends.html",
        trend_data=list(trend_data.values()),
        start_date=start_date_str,
        end_date=end_date_str,
        activity_id=activity_id,
        dimensions=dimensions,
        gaia_display_name=cfg.gaia_display_name,
        dimension_options={
            "detail.minPrice": "最低价格",
            "detail.maxPrice": "最高价格",
            "detail.minSize": "最小人数",
            "detail.maxSize": "最大人数",
            "detail.surplusSize": "剩余名额",
            "times.count": "团期数量",
        }
    )


@app.route("/gaia/activity/<activity_id>")
def gaia_activity_detail(activity_id: str):
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date
    date_key = request.args.get("date", _date.today().isoformat())

    sql = """
        SELECT activity_data, type
        FROM activity_detail
        WHERE activity_id = %s AND date_key = %s AND platform = %s
        LIMIT 1
    """

    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (activity_id, date_key, "gaia"))
            row = cur.fetchone()
            if not row:
                cfg = BaseConfig.from_env()
                return render_template("gaia_activity_detail.html",
                                      title="未找到数据",
                                      activity_id=activity_id,
                                      date_key=date_key,
                                      catalog_name="",
                                      gaia_display_name=cfg.gaia_display_name,
                                      min_price=None,
                                      max_price=None,
                                      min_size=None,
                                      max_size=None,
                                      surplus_size=None,
                                      times=[],
                                      times_count=0)

            activity_data, catalog = row

    # Gaia 分类名称映射
    catalog_names = {
        "E": "国际旅行", "L": "长途旅行", "SW": "超级周末",
        "S": "短途旅行", "WE": "城市活动", "SY": "青春系列"
    }

    detail = activity_data.get("detail", {})
    times_data = activity_data.get("times", [])

    title = detail.get("heading", "")
    min_price = detail.get("minPrice")
    max_price = detail.get("maxPrice")
    min_size = detail.get("minSize")
    max_size = detail.get("maxSize")
    surplus_size = detail.get("surplusSize")
    catalog_name = catalog_names.get(catalog, catalog)

    # 处理团期数据
    times = []
    for t in times_data:
        trip_wide_list = t.get("tripWideList", [])
        for trip in trip_wide_list:
            times.append({
                "start_date": t.get("startDate", ""),
                "end_date": t.get("endDate", ""),
                "min_price": t.get("minPrice", 0),
                "max_price": t.get("maxPrice", 0),
                "price": trip.get("price", 0),
                "max_size": trip.get("maxSize", 0),
                "order_size": trip.get("orderSize", 0),
                "surplus_size": trip.get("surplusSize", 0),
            })

    cfg = BaseConfig.from_env()
    return render_template(
        "gaia_activity_detail.html",
        title=title,
        activity_id=activity_id,
        date_key=date_key,
        catalog_name=catalog_name,
        gaia_display_name=cfg.gaia_display_name,
        min_price=float(min_price) if min_price else None,
        max_price=float(max_price) if max_price else None,
        min_size=min_size,
        max_size=max_size,
        surplus_size=surplus_size,
        times=times,
        times_count=len(times),
    )


@app.route("/tiga/trends")
def tiga_trends():
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date, timedelta

    # 默认日期范围为过去7天
    end_date = _date.today()
    start_date = end_date - timedelta(days=6)

    start_date_str = request.args.get("start_date", start_date.isoformat())
    end_date_str = request.args.get("end_date", end_date.isoformat())
    activity_id = request.args.get("activity_id", "").strip()
    dimensions = request.args.getlist("dimensions") or [
        "collect_count", "total_comment.count", "total_comment.average",
        "activityType.one_week_uv", "activityType.two_month_uv", "activityType.history_signup_count"
    ]

    where_sql = "WHERE date_key >= %s AND date_key <= %s AND platform = %s"
    params = [start_date_str, end_date_str, "tiga"]

    if activity_id:
        where_sql += " AND activity_id = %s"
        params.append(activity_id)

    sql = f"""
        SELECT activity_id,
               activity_data->>'title' AS title,
               date_key,
               COALESCE(NULLIF(activity_data->>'collect_count','')::int, 0) AS collect_count,
               COALESCE(NULLIF(activity_data->'total_comment'->>'count','')::int, 0) AS total_comment_count,
               NULLIF(activity_data->'total_comment'->>'average','')::numeric AS total_comment_average,
               COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'one_week_uv','')::int, 0) AS one_week_uv,
               COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'two_month_uv','')::int, 0) AS two_month_uv,
               COALESCE(NULLIF(activity_data->'activity_times'->'times'->0->'status'->'activityType'->>'history_signup_count','')::int, 0) AS history_signup_count
        FROM activity_detail
        {where_sql}
        ORDER BY activity_id, date_key
    """

    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [
                {
                    "activity_id": r[0],
                    "title": r[1] or "",
                    "date_key": r[2],
                    "collect_count": r[3] or 0,
                    "total_comment_count": r[4] or 0,
                    "total_comment_average": float(r[5]) if r[5] is not None else None,
                    "one_week_uv": r[6] or 0,
                    "two_month_uv": r[7] or 0,
                    "history_signup_count": r[8] or 0,
                }
                for r in cur.fetchall()
            ]

    # 组织数据按activity_id分组
    trend_data = {}
    for row in rows:
        aid = row["activity_id"]
        if aid not in trend_data:
            trend_data[aid] = {
                "title": row["title"],
                "activity_id": aid,
                "dates": [],
                "data": {dim: [] for dim in dimensions}
            }

        trend_data[aid]["dates"].append(row["date_key"])
        for dim in dimensions:
            key = dim.replace(".", "_").replace("activityType.", "")
            trend_data[aid]["data"][dim].append(row.get(key, 0))

    cfg = BaseConfig.from_env()
    return render_template(
        "tiga_trends.html",
        trend_data=list(trend_data.values()),
        start_date=start_date_str,
        end_date=end_date_str,
        activity_id=activity_id,
        dimensions=dimensions,
        tiga_display_name=cfg.tiga_display_name,
        dimension_options={
            "collect_count": "收藏人数",
            "total_comment.count": "评论人数",
            "total_comment.average": "评论平均分",
            "activityType.one_week_uv": "活动周访客数",
            "activityType.two_month_uv": "活动月访客数",
            "activityType.history_signup_count": "历史报名人数",
        }
    )


@app.route("/tiga/activity/<activity_id>")
def tiga_activity_detail(activity_id: str):
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date
    date_key = request.args.get("date", _date.today().isoformat())

    sql = """
        SELECT activity_data
        FROM activity_detail
        WHERE activity_id = %s AND date_key = %s AND platform = %s
        LIMIT 1
    """
    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (activity_id, date_key, "tiga"))
            row = cur.fetchone()
            if not row:
                cfg = BaseConfig.from_env()
                return render_template("tiga_activity_detail.html",
                                      title="未找到数据",
                                      activity_id=activity_id,
                                      date_key=date_key,
                                      tiga_display_name=cfg.tiga_display_name,
                                      default_min_person="-",
                                      default_max_person="-",
                                      times=[],
                                      times_count=0)
            activity = row[0]

    def _get(d, path, default=None):
        cur = d
        for p in path:
            if isinstance(cur, list):
                try:
                    idx = int(p)
                    cur = cur[idx]
                except Exception:
                    return default
            elif isinstance(cur, dict):
                if p in cur:
                    cur = cur[p]
                else:
                    return default
            else:
                return default
        return cur

    title = activity.get("title") or ""
    times_arr = (activity.get("activity_times") or {}).get("times") or []
    default_min_person = _get(times_arr, ["0", "status", "activityType", "default_min_person"], None)
    default_max_person = _get(times_arr, ["0", "status", "activityType", "default_max_person"], None)

    times: list[dict[str, any]] = []
    for t in times_arr:
        times.append({
            "start_time": t.get("start_time"),
            "end_time": t.get("end_time"),
            "status_name": ((t.get("status") or {}).get("name")) or "",
            "signup_count": ((t.get("status") or {}).get("signup_count")) or 0,
            "money": int(t.get("money") or 0),
        })

    cfg = BaseConfig.from_env()
    return render_template(
        "tiga_activity_detail.html",
        title=title,
        activity_id=activity_id,
        date_key=date_key,
        tiga_display_name=cfg.tiga_display_name,
        default_min_person=default_min_person if default_min_person is not None else "-",
        default_max_person=default_max_person if default_max_person is not None else "-",
        times=times,
        times_count=len(times),
    )


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    cfg = BaseConfig.from_env()
    app.secret_key = cfg.secret_key
    return app




if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
