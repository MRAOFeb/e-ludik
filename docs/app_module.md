# Модуль `app`

## Package-level declarations

### Типы

- `app` — `Bottle` приложение.
- `get_db()` — функция получения соединения с базой данных.
- `db_conn()` — контекстный менеджер для работы с транзакциями.
- `init_db()` — функция инициализации схемы базы данных.
- `hash_password(password, salt=None)` — функция хеширования пароля.
- `verify_password(password, stored_hash)` — проверка хеша пароля.
- `require_auth(handler)` — декоратор для защищенных маршрутов.

## Основные компоненты

### Инициализация

`BASE_DIR`, `DB_PATH`, `VIEWS_PATH`, `STATIC_PATH`, `SESSION_SECRET`, `PBKDF2_ROUNDS`, `USERNAME_PATTERN`

### База данных

- `users`
- `bets`
- `friends`

### Сессии

- `set_user_session(user_id)` — сохраняет сессионную cookie.
- `clear_user_session()` — удаляет сессию.
- `get_current_user()` — возвращает текущего пользователя.

### Логика статистики

- `user_stats(conn, user_id)` — рассчитывает рыночные метрики:
  - `total_bets`
  - `wins`
  - `losses`
  - `pending`
  - `total_stake`
  - `net_profit`
  - `win_rate`
  - `roi`

- `build_leaderboard(conn, user_id)` — строит рейтинг пользователя и друзей.

## Маршруты

### Обзор

- `GET /` — корневая страница, перенаправляет на `/dashboard` или `/login`.
- `GET /register`, `POST /register` — регистрация пользователя.
- `GET /login`, `POST /login` — вход в систему.
- `GET /logout` — выход.
- `GET /dashboard` — личный кабинет.
- `POST /bets/add` — добавление ставки.
- `POST /profile/update` — обновление профиля.
- `POST /friends/add` — добавление друга.
- `POST /friends/remove/<friend_id:int>` — удаление друга.
- `GET /compare` — сравнение результатов.
- `GET /rules` — правила ставок.
- `GET /u/<username>` — публичный профиль.

### Особенности

- Авторизация защищена декоратором `require_auth`.
- `redirect_with_notice` используется для передачи уведомлений между страницами.
- `parse_float` помогает корректно считывать числовые значения из форм.

## Ключевые функции

```python
@app.post("/bets/add")
@require_auth
def add_bet():
    # добавление новой ставки, валидация входных данных,
    # расчёт выплаты и запись в таблицу bets.
```

```python
@app.get("/u/<username:re:[A-Za-z0-9_]{3,24}>")
def public_profile(username):
    # показывает публичный профиль пользователя и его историю ставок.
```

## Советы разработчику

- Вынести работу с базой данных в отдельный модуль `db.py`.
- Разделить маршруты на компоненты (auth, bets, profile и т.п.).
- Добавить unit-тесты для валидации данных и маршрутов.
