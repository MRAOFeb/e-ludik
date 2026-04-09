% rebase("base.tpl", title="Кабинет | E-LUDIK", current_user=current_user, notice=notice)
<section class="hero-card">
    <div>
        <p class="kicker">личный кабинет</p>
        <h1>@{{current_user['username']}}</h1>
        <p class="muted">
            Профиль открыт для всех по ссылке:
            <a href="/u/{{current_user['username']}}" target="_blank">/u/{{current_user['username']}}</a>
        </p>
    </div>
    <a href="/u/{{current_user['username']}}" class="btn btn-ghost" target="_blank">Открыть публичный профиль</a>
</section>

<section class="stats-grid">
    <article class="stat-card">
        <p>Всего ставок</p>
        <h2>{{stats['total_bets']}}</h2>
    </article>
    <article class="stat-card">
        <p>Винрейт</p>
        <h2>{{stats['win_rate']}}%</h2>
    </article>
    <article class="stat-card">
        <p>Чистая прибыль</p>
        % profit_class = "good" if stats["net_profit"] >= 0 else "bad"
        <h2 class="{{profit_class}}">{{"{:+.2f}".format(stats["net_profit"])}}</h2>
    </article>
    <article class="stat-card">
        <p>ROI</p>
        % roi_class = "good" if stats["roi"] >= 0 else "bad"
        <h2 class="{{roi_class}}">{{"{:+.1f}".format(stats["roi"])}}%</h2>
    </article>
</section>

<section class="dashboard-grid">
    <div class="col-main">
        <article class="card">
            <h3>Новая ставка</h3>
            <form method="post" action="/bets/add" class="form-grid" data-bet-form>
                <label>
                    <span>Название ставки</span>
                    <input type="text" name="title" maxlength="120" placeholder="Например: Тотал карт больше 2.5" required />
                </label>
                <label>
                    <span>Дисциплина / матч</span>
                    <input type="text" name="game" maxlength="80" placeholder="CS2 / Team A vs Team B" required />
                </label>
                <label>
                    <span>Коэффициент</span>
                    <input type="number" name="odds" step="0.01" min="1.01" placeholder="1.85" required />
                </label>
                <label>
                    <span>Сумма ставки</span>
                    <input type="number" name="stake" step="0.01" min="0.1" placeholder="1000" required />
                </label>
                <label>
                    <span>Результат</span>
                    <select name="result" data-result>
                        <option value="pending">В процессе</option>
                        <option value="win">Выигрыш</option>
                        <option value="lose">Проигрыш</option>
                    </select>
                </label>
                <label>
                    <span>Выплата (если выигрыш)</span>
                    <input type="number" name="payout" data-payout step="0.01" min="0" placeholder="Авто: ставка × коэф." />
                </label>
                <label class="full">
                    <span>Комментарий</span>
                    <textarea name="description" rows="3" maxlength="350" placeholder="Кратко: почему делал ставку, эмоции, выводы."></textarea>
                </label>
                <button type="submit" class="btn full">Добавить в историю</button>
            </form>
        </article>

        <article class="card">
            <h3>Мои последние ставки</h3>
            % if my_bets:
                <div class="table-wrap">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Ставка</th>
                                <th>Коэф / сумма</th>
                                <th>Результат</th>
                                <th>Профит</th>
                            </tr>
                        </thead>
                        <tbody>
                            % for bet in my_bets:
                                % if bet["result"] == "win":
                                    % profit = bet["payout"] - bet["stake"]
                                % elif bet["result"] == "lose":
                                    % profit = -bet["stake"]
                                % else:
                                    % profit = 0
                                % end
                                % result_label = {"win": "Выигрыш", "lose": "Проигрыш", "pending": "В процессе"}[bet["result"]]
                                % profit_class = "good" if profit > 0 else ("bad" if profit < 0 else "")
                                <tr>
                                    <td>{{bet["created_at"][:16]}}</td>
                                    <td>
                                        <strong>{{bet["title"]}}</strong>
                                        <div class="small-muted">{{bet["game"]}}</div>
                                    </td>
                                    <td>{{"{:.2f}".format(bet["odds"])}} / {{"{:.2f}".format(bet["stake"])}}</td>
                                    <td><span class="pill pill-{{bet['result']}}">{{result_label}}</span></td>
                                    <td class="{{profit_class}}">{{"{:+.2f}".format(profit)}}</td>
                                </tr>
                            % end
                        </tbody>
                    </table>
                </div>
            % else:
                <p class="muted">Пока нет ставок. Добавь первую в форме выше.</p>
            % end
        </article>
    </div>

    <div class="col-side">
        <article class="card">
            <h3>Друзья-лудики</h3>
            <form method="post" action="/friends/add" class="inline-form">
                <input type="hidden" name="next" value="/dashboard" />
                <input type="text" name="friend_username" placeholder="Ник друга" required />
                <button type="submit" class="btn">Добавить</button>
            </form>
            % if friend_suggestions:
                <p class="small-muted">Можно добавить быстро:</p>
                <div class="chip-list">
                    % for suggestion in friend_suggestions:
                        <form method="post" action="/friends/add">
                            <input type="hidden" name="friend_username" value="{{suggestion['username']}}" />
                            <input type="hidden" name="next" value="/dashboard" />
                            <button type="submit" class="chip-btn">@{{suggestion['username']}}</button>
                        </form>
                    % end
                </div>
            % end
            % if friends:
                <ul class="friend-list">
                    % for friend in friends:
                        <li>
                            <a href="/u/{{friend['username']}}" target="_blank">@{{friend["username"]}}</a>
                            <form method="post" action="/friends/remove/{{friend['id']}}">
                                <input type="hidden" name="next" value="/dashboard" />
                                <button type="submit" class="btn-link" data-confirm="Убрать из друзей?">Убрать</button>
                            </form>
                        </li>
                    % end
                </ul>
            % else:
                <p class="muted">Пока друзей нет. Добавь первых для сравнения результатов.</p>
            % end
        </article>

        <article class="card">
            <div class="card-head">
                <h3>Сравнение результатов</h3>
                <a href="/compare">Полная таблица</a>
            </div>
            <div class="table-wrap">
                <table class="data-table compact">
                    <thead>
                        <tr>
                            <th>Игрок</th>
                            <th>Винрейт</th>
                            <th>Профит</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for row in leaderboard:
                            % row_class = "me-row" if row["id"] == current_user["id"] else ""
                            % profit_class = "good" if row["stats"]["net_profit"] >= 0 else "bad"
                            <tr class="{{row_class}}">
                                <td><a href="/u/{{row['username']}}" target="_blank">@{{row["username"]}}</a></td>
                                <td>{{row["stats"]["win_rate"]}}%</td>
                                <td class="{{profit_class}}">{{"{:+.2f}".format(row["stats"]["net_profit"])}}</td>
                            </tr>
                        % end
                    </tbody>
                </table>
            </div>
        </article>

        <article class="card">
            <h3>Активность друзей</h3>
            % if friends_activity:
                <ul class="activity-list">
                    % for item in friends_activity:
                        % label = {"win": "выиграл", "lose": "проиграл", "pending": "ожидает"}[item["result"]]
                        <li>
                            <a href="/u/{{item['username']}}" target="_blank">@{{item["username"]}}</a>
                            <span>{{label}}</span>
                            <strong>{{item["title"]}}</strong>
                            <em>{{item["created_at"][:16]}}</em>
                        </li>
                    % end
                </ul>
            % else:
                <p class="muted">Пока в ленте тихо. Добавь друзей, чтобы видеть их ставки.</p>
            % end
        </article>

        <article class="card">
            <h3>Настройки профиля</h3>
            <form method="post" action="/profile/update" class="form-stack">
                <label>
                    <span>Ссылка на аватар</span>
                    <input type="url" name="avatar_url" value="{{current_user['avatar_url']}}" placeholder="https://..." />
                </label>
                <label>
                    <span>Био</span>
                    <textarea name="bio" rows="4" maxlength="280" placeholder="Коротко о себе">{{current_user["bio"]}}</textarea>
                </label>
                <button type="submit" class="btn">Сохранить профиль</button>
            </form>
        </article>
    </div>
</section>
