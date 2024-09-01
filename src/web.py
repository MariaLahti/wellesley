from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import logging

from flask import Flask, request, render_template_string, redirect, url_for, session, abort
import psycopg

from .config import load_config


app = Flask(__name__)
log = logging.getLogger(__name__)


TABLE_HTML = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>活动分析面板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background:#0b1220; color:#e5e7eb; }
      .container { padding-top:24px; }
      .card { background:#0f172a; border:1px solid #1f2937; }
      .table { color:#e5e7eb; }
      a, a:visited { color:#60a5fa; }
      h3.card-title { color:#ffffff; }
      .form-control, .form-select { background:#0f172a; color:#e5e7eb; border-color:#334155; }
      .form-control::placeholder { color:#94a3b8; }
      .btn-primary { background:#3b82f6; border-color:#3b82f6; }
      th a { text-decoration:none; color:#93c5fd; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card shadow-sm">
        <div class="card-body">
          <h3 class="card-title mb-3">活动分析面板</h3>
          <form class="row gy-2 gx-3 align-items-center mb-3" method="get">
            <div class="col-sm-4">
              <input type="text" class="form-control" name="q" placeholder="按标题筛选" value="{{ q }}">
            </div>
            <div class="col-sm-3">
              <select class="form-select" name="sort">
                {% for key, label in sort_options.items() %}
                  <option value="{{ key }}" {% if key==sort %}selected{% endif %}>按 {{ label }} 排序</option>
                {% endfor %}
              </select>
            </div>
            <div class="col-sm-2">
              <select class="form-select" name="order">
                <option value="desc" {% if order=='desc' %}selected{% endif %}>降序</option>
                <option value="asc" {% if order=='asc' %}selected{% endif %}>升序</option>
              </select>
            </div>
            <div class="col-sm-2">
              <select class="form-select" name="type">
                <option value="all" {% if type_filter=='all' %}selected{% endif %}>全部</option>
                <option value="domestic" {% if type_filter=='domestic' %}selected{% endif %}>境内</option>
                <option value="overseas" {% if type_filter=='overseas' %}selected{% endif %}>境外</option>
              </select>
            </div>
            <div class="col-sm-3">
              <input type="date" class="form-control" name="date" value="{{ date_key }}">
            </div>
            <div class="col-sm-2">
              <button type="submit" class="btn btn-primary w-100">应用</button>
            </div>
          </form>

          <div class="table-responsive">
            <table class="table table-dark table-hover align-middle">
              <thead>
                <tr>
                  <th>活动ID</th>
                  <th>标题</th>
                  <th><a href="?{{ query_with('sort','collect_count') }}">收藏数</a></th>
                  <th><a href="?{{ query_with('sort','total_comment.count') }}">评论数</a></th>
                  <th><a href="?{{ query_with('sort','total_comment.average') }}">评分</a></th>
                  <th><a href="?{{ query_with('sort','activityType.one_week_uv') }}">周UV</a></th>
                  <th><a href="?{{ query_with('sort','activityType.two_month_uv') }}">月UV</a></th>
                  <th><a href="?{{ query_with('sort','activityType.history_signup_count') }}">历史报名</a></th>
                  <th>数据日期</th>
                </tr>
              </thead>
              <tbody>
                {% for row in rows %}
                <tr>
                  <td>{{ row.activity_id }}</td>
                  <td><a href="/activity/{{ row.activity_id }}?date={{ date_key }}" target="_blank">{{ row.title }}</a></td>
                  <td>{{ row.collect_count }}</td>
                  <td>{{ row.total_comment_count }}</td>
                  <td>{{ row.total_comment_average }}</td>
                  <td>{{ row.one_week_uv }}</td>
                  <td>{{ row.two_month_uv }}</td>
                  <td>{{ row.history_signup_count }}</td>
                  <td>{{ row.date_key }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </body>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </html>
"""


LOGIN_HTML = """
<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>登录</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>
      body { background:#0b1220; color:#e5e7eb; }
      .card { background:#0f172a; border:1px solid #1f2937; }
      .form-control { background:#0f172a; color:#e5e7eb; border-color:#334155; }
      .btn-primary { background:#3b82f6; border-color:#3b82f6; }
    </style>
  </head>
  <body>
    <div class=\"container\" style=\"max-width:420px; padding-top:80px;\">
      <div class=\"card shadow-sm\">
        <div class=\"card-body\">
          <h4 class=\"mb-3\">登录</h4>
          {% if error %}
            <div class=\"alert alert-danger\" role=\"alert\">{{ error }}</div>
          {% endif %}
          <form method=\"post\">
            <div class=\"mb-3\">
              <label class=\"form-label\">账号</label>
              <input class=\"form-control\" name=\"username\" autocomplete=\"username\">
            </div>
            <div class=\"mb-3\">
              <label class=\"form-label\">密码</label>
              <input type=\"password\" class=\"form-control\" name=\"password\" autocomplete=\"current-password\">
            </div>
            <button type=\"submit\" class=\"btn btn-primary w-100\">登录</button>
          </form>
        </div>
      </div>
    </div>
  </body>
  <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js\"></script>
  </html>
"""


def pg_connect():
    cfg = load_config()
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
    cfg = load_config()
    if not cfg.web_username or not cfg.web_password:
        return True
    return session.get("authed") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    cfg = load_config()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if cfg.web_username and cfg.web_password and username == cfg.web_username and password == cfg.web_password:
            session["authed"] = True
            return redirect(url_for("index"))
        return render_template_string(LOGIN_HTML, error="账号或密码错误")
    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
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

    where_sql = "WHERE date_key = %s"
    params: List[Any] = [date_key]
    if q:
        where_sql += " AND activity_data->>'title' ILIKE %s"
        params.append(f"%{q}%")
    if type_filter in ("domestic", "overseas"):
        where_sql += " AND type = %s"
        params.append(type_filter)

    sql = f"""
        SELECT activity_id,
               date_key,
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
                    "title": r[2] or "",
                    "collect_count": r[3] or 0,
                    "total_comment_count": r[4] or 0,
                    "total_comment_average": float(r[5]) if r[5] is not None else None,
                    "one_week_uv": r[6] or 0,
                    "two_month_uv": r[7] or 0,
                    "history_signup_count": r[8] or 0,
                }
                for r in cur.fetchall()
            ]

    return render_template_string(
        TABLE_HTML,
        rows=rows,
        q=q,
        sort=sort,
        order=order,
        date_key=date_key,
        type_filter=type_filter,
        sort_options={
            "collect_count": "收藏人数",
            "total_comment.count": "评论人数",
            "total_comment.average": "评论平均分",
            "activityType.one_week_uv": "活动周访客数",
            "activityType.two_month_uv": "活动月访客数",
            "activityType.history_signup_count": "历史报名人数",
        },
    )


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    cfg = load_config()
    app.secret_key = cfg.secret_key
    return app

# ------------------------ Activity Detail Page ------------------------

DETAIL_HTML = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>活动详情</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background:#0b1220; color:#e5e7eb; }
      .container { padding-top:24px; }
      .card { background:#0f172a; border:1px solid #1f2937; }
      .table { color:#e5e7eb; }
      a, a:visited { color:#60a5fa; }
      h3.card-title { color:#ffffff; }
      h5.card-title { color:#ffffff; }
      .meta { color:#94a3b8; }
      .meta .value { color:#ffffff; }
      .badge { background:#2563eb; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card shadow-sm mb-3">
        <div class="card-body">
          <h3 class="card-title mb-2">{{ title }}</h3>
          <div class="meta">活动ID：<span class="badge">{{ activity_id }}</span></div>
          <div class="mt-2 meta">最小成行人数：<span class="value">{{ default_min_person }}</span>；最大成行人数：<span class="value">{{ default_max_person }}</span></div>
          <div class="mt-1 meta">数据日期：<span class="value">{{ date_key }}</span></div>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-3">活动期次（{{ times_count }} 个）</h5>
          <div class="table-responsive">
            <table class="table table-dark table-hover align-middle">
              <thead>
                <tr>
                  <th>开始日期</th>
                  <th>结束日期</th>
                  <th>状态</th>
                  <th>报名人数</th>
                </tr>
              </thead>
              <tbody>
                {% for t in times %}
                <tr>
                  <td>{{ t.start_time }}</td>
                  <td>{{ t.end_time }}</td>
                  <td>{{ t.status_name }}</td>
                  <td>{{ t.signup_count }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </body>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </html>
"""


@app.route("/activity/<activity_id>")
def activity_detail(activity_id: str):
    if not _require_login():
        return redirect(url_for("login"))
    from datetime import date as _date
    date_key = request.args.get("date", _date.today().isoformat())
    sql = """
        SELECT activity_data
        FROM activity_detail
        WHERE activity_id = %s AND date_key = %s
        LIMIT 1
    """
    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (activity_id, date_key))
            row = cur.fetchone()
            if not row:
                return render_template_string(DETAIL_HTML,
                                              title="未找到数据",
                                              activity_id=activity_id,
                                              date_key=date_key,
                                              default_min_person="-",
                                              default_max_person="-",
                                              times=[])
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
        })

    return render_template_string(
        DETAIL_HTML,
        title=title,
        activity_id=activity_id,
        date_key=date_key,
        default_min_person=default_min_person if default_min_person is not None else "-",
        default_max_person=default_max_person if default_max_person is not None else "-",
        times=times,
        times_count=len(times),
    )


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)


