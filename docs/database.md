# База данных

## Package-level declarations

База данных SQLite не является Python-модулем, но её структура важна для разработчика.

### Таблицы

- `users`
- `bets`
- `friends`

## Описание таблиц

### `users`

- `id` — PRIMARY KEY
- `username` — уникальный никнейм
- `password_hash` — хеш пароля
- `bio` — биография
- `avatar_url` — ссылка на аватар
- `created_at` — дата создания

### `bets`

- `id` — PRIMARY KEY
- `user_id` — ссылка на пользователя
- `title` — название ставки
- `game` — дисциплина/матч
- `odds` — коэффициент
- `stake` — сумма
- `result` — результат
- `payout` — выплата
- `description` — комментарий
- `created_at` — дата записи

### `friends`

- `id` — PRIMARY KEY
- `user_id` — пользователь
- `friend_id` — друг
- `created_at` — дата добавления

## Внешние ключи

- `bets.user_id` → `users.id`
- `friends.user_id` → `users.id`
- `friends.friend_id` → `users.id`

## Примечания

- `ON DELETE CASCADE` гарантирует удаление зависимых записей.
- Схема создаётся в `init_db()` в `app.py`.
