<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{{title}}</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <script defer src="/static/app.js"></script>
</head>
<body>
    <div class="glow glow-left"></div>
    <div class="glow glow-right"></div>
    <header class="topbar">
        <a href="/" class="brand">
            <span class="brand-main">E-LUDIK</span>
            <span class="brand-sub">bet social</span>
        </a>
        <nav class="top-nav">
            <a href="/rules">Правила</a>
            % if current_user:
                <a href="/dashboard">Кабинет</a>
                <a href="/compare">Сравнение</a>
                <a href="/u/{{current_user['username']}}" target="_blank">Публичный профиль</a>
                <a href="/logout">Выйти</a>
            % else:
                <a href="/login">Вход</a>
                <a href="/register">Регистрация</a>
            % end
        </nav>
    </header>
    <main class="page-wrap">
        % if notice:
            <div class="notice notice-{{notice['level']}}">
                {{notice['text']}}
            </div>
        % end
        {{!base}}
    </main>
</body>
</html>
