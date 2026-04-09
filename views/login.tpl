% rebase("base.tpl", title="Вход | E-LUDIK", current_user=current_user, notice=notice)
<section class="auth-shell">
    <div class="auth-card">
        <p class="kicker">соцсеть ставок</p>
        <h1>Вход в аккаунт</h1>
        <p class="muted">Веди историю ставок, сравнивай статистику с друзьями и делись публичным профилем.</p>
        <form method="post" action="/login" class="form-stack">
            <label>
                <span>Ник</span>
                <input type="text" name="username" placeholder="например: cyber_ludik" required />
            </label>
            <label>
                <span>Пароль</span>
                <input type="password" name="password" placeholder="Минимум 6 символов" required />
            </label>
            <button type="submit" class="btn">Войти</button>
        </form>
        <p class="helper-line">Нет аккаунта? <a href="/register">Зарегистрироваться</a></p>
    </div>
</section>
