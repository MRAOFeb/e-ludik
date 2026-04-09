% rebase("base.tpl", title="Профиль @" + profile_user["username"] + " | E-LUDIK", current_user=current_user, notice=notice)
<section class="hero-card profile-head">
    <div class="profile-ident">
        % avatar = profile_user["avatar_url"] if profile_user["avatar_url"] else "/static/default-avatar.svg"
        <img src="{{avatar}}" alt="avatar" class="avatar" />
        <div>
            <p class="kicker">публичный кабинет</p>
            <h1>@{{profile_user["username"]}}</h1>
            % if profile_user["bio"]:
                <p class="muted">{{profile_user["bio"]}}</p>
            % else:
                <p class="muted">Пользователь пока не добавил описание.</p>
            % end
        </div>
    </div>
    <div class="profile-actions">
        % if current_user and current_user["id"] == profile_user["id"]:
            <a href="/dashboard" class="btn">Редактировать в кабинете</a>
        % elif current_user and not is_friend:
            <form method="post" action="/friends/add">
                <input type="hidden" name="friend_username" value="{{profile_user['username']}}" />
                <input type="hidden" name="next" value="/u/{{profile_user['username']}}" />
                <button type="submit" class="btn">Добавить в друзья</button>
            </form>
        % elif current_user and is_friend:
            <span class="pill pill-win">Уже в друзьях</span>
        % else:
            <a href="/register" class="btn">Создать аккаунт</a>
        % end
    </div>
</section>

<section class="stats-grid">
    <article class="stat-card">
        <p>Всего ставок</p>
        <h2>{{profile_stats["total_bets"]}}</h2>
    </article>
    <article class="stat-card">
        <p>Винрейт</p>
        <h2>{{profile_stats["win_rate"]}}%</h2>
    </article>
    <article class="stat-card">
        <p>Прибыль</p>
        % profit_class = "good" if profile_stats["net_profit"] >= 0 else "bad"
        <h2 class="{{profit_class}}">{{"{:+.2f}".format(profile_stats["net_profit"])}}</h2>
    </article>
    <article class="stat-card">
        <p>ROI</p>
        % roi_class = "good" if profile_stats["roi"] >= 0 else "bad"
        <h2 class="{{roi_class}}">{{"{:+.1f}".format(profile_stats["roi"])}}%</h2>
    </article>
</section>

<section class="card">
    <h3>История ставок</h3>
    % if profile_bets:
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
                    % for bet in profile_bets:
                        % if bet["result"] == "win":
                            % profit = bet["payout"] - bet["stake"]
                        % elif bet["result"] == "lose":
                            % profit = -bet["stake"]
                        % else:
                            % profit = 0
                        % end
                        % label = {"win": "Выигрыш", "lose": "Проигрыш", "pending": "В процессе"}[bet["result"]]
                        % profit_class = "good" if profit > 0 else ("bad" if profit < 0 else "")
                        <tr>
                            <td>{{bet["created_at"][:16]}}</td>
                            <td>
                                <strong>{{bet["title"]}}</strong>
                                <div class="small-muted">{{bet["game"]}}</div>
                            </td>
                            <td>{{"{:.2f}".format(bet["odds"])}} / {{"{:.2f}".format(bet["stake"])}}</td>
                            <td><span class="pill pill-{{bet['result']}}">{{label}}</span></td>
                            <td class="{{profit_class}}">{{"{:+.2f}".format(profit)}}</td>
                        </tr>
                    % end
                </tbody>
            </table>
        </div>
    % else:
        <p class="muted">История ставок пуста.</p>
    % end
</section>
