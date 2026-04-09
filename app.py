import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from functools import wraps
from urllib.parse import urlencode

from bottle import Bottle, TEMPLATE_PATH, redirect, request, response, run, static_file, template


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "socialbets.db")
VIEWS_PATH = os.path.join(BASE_DIR, "views")
STATIC_PATH = os.path.join(BASE_DIR, "static")

SESSION_SECRET = os.environ.get("SESSION_SECRET", "change-this-session-secret")
PBKDF2_ROUNDS = 200_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,24}$")

app = Bottle()
TEMPLATE_PATH.insert(0, VIEWS_PATH)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_conn():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                bio TEXT NOT NULL DEFAULT '',
                avatar_url TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                game TEXT NOT NULL,
                odds REAL NOT NULL CHECK(odds >= 1.01),
                stake REAL NOT NULL CHECK(stake >= 0.1),
                result TEXT NOT NULL CHECK(result IN ('win', 'lose', 'pending')),
                payout REAL NOT NULL DEFAULT 0 CHECK(payout >= 0),
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, friend_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(friend_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ROUNDS
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored_hash):
    try:
        salt, _ = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, stored_hash)


def get_notice():
    text = request.query.getunicode("msg", "").strip()
    if not text:
        return None
    level = request.query.get("level", "info").strip().lower()
    if level not in {"info", "warn", "error", "success"}:
        level = "info"
    return {"text": text, "level": level}


def redirect_with_notice(path, message, level="info"):
    query = urlencode({"msg": message, "level": level})
    separator = "&" if "?" in path else "?"
    redirect(f"{path}{separator}{query}")


def parse_float(form_value):
    if form_value is None:
        return None
    value = str(form_value).strip().replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def set_user_session(user_id):
    response.set_cookie(
        "session",
        str(user_id),
        secret=SESSION_SECRET,
        path="/",
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
    )


def clear_user_session():
    response.delete_cookie("session", path="/")


def get_current_user():
    raw_user_id = request.get_cookie("session", secret=SESSION_SECRET)
    if not raw_user_id:
        return None
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return None
    with db_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def require_auth(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            redirect_with_notice("/login", "Сначала войдите в аккаунт.", "warn")
        return handler(*args, **kwargs)

    return wrapper


def user_stats(conn, user_id):
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_bets,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'lose' THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN result = 'pending' THEN 1 ELSE 0 END) AS pending,
            COALESCE(SUM(stake), 0) AS total_stake,
            COALESCE(
                SUM(
                    CASE
                        WHEN result = 'win' THEN payout - stake
                        WHEN result = 'lose' THEN -stake
                        ELSE 0
                    END
                ),
                0
            ) AS net_profit
        FROM bets
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    wins = int(row["wins"] or 0)
    losses = int(row["losses"] or 0)
    settled = wins + losses
    total_stake = float(row["total_stake"] or 0)
    net_profit = float(row["net_profit"] or 0)
    win_rate = (wins * 100 / settled) if settled else 0
    roi = (net_profit * 100 / total_stake) if total_stake else 0

    return {
        "total_bets": int(row["total_bets"] or 0),
        "wins": wins,
        "losses": losses,
        "pending": int(row["pending"] or 0),
        "total_stake": round(total_stake, 2),
        "net_profit": round(net_profit, 2),
        "win_rate": round(win_rate, 1),
        "roi": round(roi, 1),
    }


def build_leaderboard(conn, user_id):
    friend_rows = conn.execute(
        "SELECT friend_id FROM friends WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()

    participant_ids = [user_id]
    participant_ids.extend(row["friend_id"] for row in friend_rows)
    unique_ids = list(dict.fromkeys(participant_ids))

    leaderboard = []
    for participant_id in unique_ids:
        user = conn.execute(
            "SELECT id, username FROM users WHERE id = ?", (participant_id,)
        ).fetchone()
        if not user:
            continue
        stats = user_stats(conn, participant_id)
        leaderboard.append(
            {
                "id": user["id"],
                "username": user["username"],
                "stats": stats,
            }
        )

    leaderboard.sort(
        key=lambda item: (
            item["stats"]["net_profit"],
            item["stats"]["roi"],
            item["stats"]["win_rate"],
        ),
        reverse=True,
    )
    return leaderboard


@app.route("/static/<filepath:path>")
def server_static(filepath):
    return static_file(filepath, root=STATIC_PATH)


@app.get("/")
def root():
    if get_current_user():
        redirect("/dashboard")
    redirect("/login")


@app.get("/register")
def register_page():
    return template("register", current_user=get_current_user(), notice=get_notice())


@app.post("/register")
def register_action():
    username = request.forms.getunicode("username", "").strip()
    password = request.forms.getunicode("password", "")
    password_repeat = request.forms.getunicode("password_repeat", "")

    if not USERNAME_PATTERN.match(username):
        redirect_with_notice(
            "/register",
            "Ник должен быть 3-24 символа: латиница, цифры и нижнее подчёркивание.",
            "error",
        )

    if len(password) < 6:
        redirect_with_notice("/register", "Пароль должен быть минимум 6 символов.", "error")

    if password != password_repeat:
        redirect_with_notice("/register", "Пароли не совпадают.", "error")

    password_hash = hash_password(password)
    try:
        with db_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            user_id = conn.execute(
                "SELECT id FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()["id"]
    except sqlite3.IntegrityError:
        redirect_with_notice(
            "/register", "Такой ник уже занят. Попробуйте другой.", "error"
        )

    set_user_session(user_id)
    redirect_with_notice("/dashboard", "Профиль создан. Добро пожаловать!", "success")


@app.get("/login")
def login_page():
    return template("login", current_user=get_current_user(), notice=get_notice())


@app.post("/login")
def login_action():
    username = request.forms.getunicode("username", "").strip()
    password = request.forms.getunicode("password", "")

    with db_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        redirect_with_notice("/login", "Неверный логин или пароль.", "error")

    set_user_session(user["id"])
    redirect_with_notice("/dashboard", "С возвращением!", "success")


@app.get("/logout")
def logout():
    clear_user_session()
    redirect_with_notice("/login", "Вы вышли из аккаунта.", "info")


@app.get("/dashboard")
@require_auth
def dashboard():
    current_user = get_current_user()
    with db_conn() as conn:
        stats = user_stats(conn, current_user["id"])
        my_bets = conn.execute(
            """
            SELECT *
            FROM bets
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT 20
            """,
            (current_user["id"],),
        ).fetchall()
        friends = conn.execute(
            """
            SELECT u.id, u.username, u.bio, u.avatar_url
            FROM friends f
            JOIN users u ON u.id = f.friend_id
            WHERE f.user_id = ?
            ORDER BY u.username COLLATE NOCASE
            """,
            (current_user["id"],),
        ).fetchall()
        friends_activity = conn.execute(
            """
            SELECT b.*, u.username
            FROM bets b
            JOIN friends f ON f.friend_id = b.user_id
            JOIN users u ON u.id = b.user_id
            WHERE f.user_id = ?
            ORDER BY datetime(b.created_at) DESC
            LIMIT 12
            """,
            (current_user["id"],),
        ).fetchall()
        friend_suggestions = conn.execute(
            """
            SELECT id, username
            FROM users
            WHERE id != ?
                AND id NOT IN (
                    SELECT friend_id
                    FROM friends
                    WHERE user_id = ?
                )
            ORDER BY username COLLATE NOCASE
            LIMIT 12
            """,
            (current_user["id"], current_user["id"]),
        ).fetchall()
        leaderboard = build_leaderboard(conn, current_user["id"])

    return template(
        "dashboard",
        current_user=current_user,
        notice=get_notice(),
        stats=stats,
        my_bets=my_bets,
        friends=friends,
        friends_activity=friends_activity,
        friend_suggestions=friend_suggestions,
        leaderboard=leaderboard,
    )


@app.get("/cabinet")
@require_auth
def cabinet_alias():
    redirect("/dashboard")


@app.get("/account")
@require_auth
def account_alias():
    redirect("/dashboard")


@app.post("/bets/add")
@require_auth
def add_bet():
    current_user = get_current_user()
    title = request.forms.getunicode("title", "").strip()
    game = request.forms.getunicode("game", "").strip()
    description = request.forms.getunicode("description", "").strip()
    result = request.forms.get("result", "pending").strip().lower()
    stake = parse_float(request.forms.get("stake"))
    odds = parse_float(request.forms.get("odds"))
    payout = parse_float(request.forms.get("payout"))

    if not title or not game:
        redirect_with_notice("/dashboard", "Заполните название ставки и дисциплину.", "error")

    if stake is None or stake < 0.1:
        redirect_with_notice("/dashboard", "Сумма ставки должна быть не меньше 0.1.", "error")

    if odds is None or odds < 1.01:
        redirect_with_notice("/dashboard", "Коэффициент должен быть не меньше 1.01.", "error")

    if result not in {"win", "lose", "pending"}:
        redirect_with_notice("/dashboard", "Некорректный результат ставки.", "error")

    if result == "win":
        if payout is None or payout <= 0:
            payout = round(stake * odds, 2)
    else:
        payout = 0.0

    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO bets (user_id, title, game, odds, stake, result, payout, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                title[:120],
                game[:80],
                float(stake),
                float(odds),
                result,
                float(payout),
                description[:350],
            ),
        )

    redirect_with_notice("/dashboard", "Ставка добавлена в историю.", "success")


@app.post("/profile/update")
@require_auth
def update_profile():
    current_user = get_current_user()
    bio = request.forms.getunicode("bio", "").strip()[:280]
    avatar_url = request.forms.getunicode("avatar_url", "").strip()[:350]

    if avatar_url and not (
        avatar_url.startswith("http://")
        or avatar_url.startswith("https://")
        or avatar_url.startswith("/static/")
    ):
        redirect_with_notice(
            "/dashboard",
            "Ссылка на аватар должна начинаться с https://, http:// или /static/.",
            "error",
        )

    with db_conn() as conn:
        conn.execute(
            "UPDATE users SET bio = ?, avatar_url = ? WHERE id = ?",
            (bio, avatar_url, current_user["id"]),
        )

    redirect_with_notice("/dashboard", "Профиль обновлён.", "success")


@app.post("/friends/add")
@require_auth
def add_friend():
    current_user = get_current_user()
    friend_username = request.forms.getunicode("friend_username", "").strip()
    next_path = request.forms.getunicode("next", "/dashboard").strip() or "/dashboard"
    if not next_path.startswith("/"):
        next_path = "/dashboard"

    if not USERNAME_PATTERN.match(friend_username):
        redirect_with_notice(next_path, "Введите корректный ник друга.", "error")

    with db_conn() as conn:
        friend = conn.execute(
            "SELECT id, username FROM users WHERE username = ? COLLATE NOCASE",
            (friend_username,),
        ).fetchone()

        if not friend:
            redirect_with_notice(next_path, "Пользователь с таким ником не найден.", "error")

        if friend["id"] == current_user["id"]:
            redirect_with_notice(next_path, "Нельзя добавить себя в друзья.", "warn")

        try:
            conn.execute(
                "INSERT INTO friends (user_id, friend_id) VALUES (?, ?)",
                (current_user["id"], friend["id"]),
            )
        except sqlite3.IntegrityError:
            redirect_with_notice(next_path, "Этот пользователь уже у вас в друзьях.", "info")

    redirect_with_notice(next_path, f"{friend['username']} добавлен в друзья.", "success")


@app.post("/friends/remove/<friend_id:int>")
@require_auth
def remove_friend(friend_id):
    current_user = get_current_user()
    next_path = request.forms.getunicode("next", "/dashboard").strip() or "/dashboard"
    if not next_path.startswith("/"):
        next_path = "/dashboard"

    with db_conn() as conn:
        conn.execute(
            "DELETE FROM friends WHERE user_id = ? AND friend_id = ?",
            (current_user["id"], friend_id),
        )

    redirect_with_notice(next_path, "Пользователь убран из друзей.", "info")


@app.get("/compare")
@require_auth
def compare():
    current_user = get_current_user()
    with db_conn() as conn:
        leaderboard = build_leaderboard(conn, current_user["id"])
    return template(
        "compare",
        current_user=current_user,
        notice=get_notice(),
        leaderboard=leaderboard,
    )


@app.get("/comparison")
@require_auth
def comparison_alias():
    redirect("/compare")


@app.get("/leaderboard")
@require_auth
def leaderboard_alias():
    redirect("/compare")


@app.get("/rules")
def rules():
    return template("rules", current_user=get_current_user(), notice=get_notice())


@app.get("/u/<username:re:[A-Za-z0-9_]{3,24}>")
def public_profile(username):
    current_user = get_current_user()
    with db_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
        if not user:
            return template(
                "not_found",
                current_user=current_user,
                notice={"text": "Профиль не найден.", "level": "error"},
            )
        bets = conn.execute(
            """
            SELECT *
            FROM bets
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT 30
            """,
            (user["id"],),
        ).fetchall()
        stats = user_stats(conn, user["id"])
        is_friend = False
        if current_user and current_user["id"] != user["id"]:
            relation = conn.execute(
                """
                SELECT 1
                FROM friends
                WHERE user_id = ? AND friend_id = ?
                """,
                (current_user["id"], user["id"]),
            ).fetchone()
            is_friend = relation is not None

    return template(
        "public_profile",
        current_user=current_user,
        notice=get_notice(),
        profile_user=user,
        profile_stats=stats,
        profile_bets=bets,
        is_friend=is_friend,
    )


@app.get("/profile/<username:re:[A-Za-z0-9_]{3,24}>")
def public_profile_alias(username):
    redirect(f"/u/{username}")


if __name__ == "__main__":
    init_db()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    debug = os.environ.get("DEBUG", "1") == "1"
    run(app=app, host=host, port=port, reloader=debug, debug=debug)
else:
    init_db()
