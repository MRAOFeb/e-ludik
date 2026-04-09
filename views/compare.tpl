% rebase("base.tpl", title="Сравнение | E-LUDIK", current_user=current_user, notice=notice)
<section class="hero-card">
    <div>
        <p class="kicker">лига друзей</p>
        <h1>Сравнение успехов</h1>
        <p class="muted">
            Таблица учитывает тебя и всех добавленных друзей. Сортировка по чистой прибыли, затем по ROI.
        </p>
    </div>
    <a href="/dashboard" class="btn btn-ghost">Вернуться в кабинет</a>
</section>

<section class="card">
    <div class="table-wrap">
        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Игрок</th>
                    <th>Ставок</th>
                    <th>Винрейт</th>
                    <th>Общий банк</th>
                    <th>Профит</th>
                    <th>ROI</th>
                </tr>
            </thead>
            <tbody>
                % for idx, row in enumerate(leaderboard, start=1):
                    % stats = row["stats"]
                    % profit_class = "good" if stats["net_profit"] >= 0 else "bad"
                    % roi_class = "good" if stats["roi"] >= 0 else "bad"
                    % me_row = "me-row" if row["id"] == current_user["id"] else ""
                    <tr class="{{me_row}}">
                        <td>{{idx}}</td>
                        <td><a href="/u/{{row['username']}}" target="_blank">@{{row["username"]}}</a></td>
                        <td>{{stats["total_bets"]}}</td>
                        <td>{{stats["win_rate"]}}%</td>
                        <td>{{"{:.2f}".format(stats["total_stake"])}}</td>
                        <td class="{{profit_class}}">{{"{:+.2f}".format(stats["net_profit"])}}</td>
                        <td class="{{roi_class}}">{{"{:+.1f}".format(stats["roi"])}}%</td>
                    </tr>
                % end
            </tbody>
        </table>
    </div>
</section>
