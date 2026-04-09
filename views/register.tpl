% rebase("base.tpl", title="Регистрация | E-LUDIK", current_user=current_user, notice=notice)
<section class="auth-shell">
    <div class="auth-card">
        <p class="kicker">новый профиль</p>
        <h1>Создать аккаунт</h1>
        <p class="muted">После регистрации твой публичный профиль будет доступен по ссылке `/u/ник`.</p>
        <form method="post" action="/register" class="form-stack">
            <label>
                <span>Ник</span>
                <input
                    type="text"
                    name="username"
                    placeholder="Латиница, цифры, _"
                    minlength="3"
                    maxlength="24"
                    pattern="[A-Za-z0-9_]{3,24}"
                    required
                />
            </label>
            <label>
                <span>Пароль</span>
                <input type="password" name="password" minlength="6" required />
            </label>
            <label>
                <span>Повтор пароля</span>
                <input type="password" name="password_repeat" minlength="6" required />
            </label>
            <button type="submit" class="btn">Создать профиль</button>
        </form>
        <p class="helper-line">Уже есть аккаунт? <a href="/login">Войти</a></p>
    </div>
</section>
