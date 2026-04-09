function setupBetForm(form) {
    var resultField = form.querySelector("[data-result]");
    var stakeField = form.querySelector('input[name="stake"]');
    var oddsField = form.querySelector('input[name="odds"]');
    var payoutField = form.querySelector("[data-payout]");

    if (!resultField || !stakeField || !oddsField || !payoutField) {
        return;
    }

    function updatePayoutState() {
        var result = resultField.value;
        var stake = Number(stakeField.value);
        var odds = Number(oddsField.value);

        if (result === "win") {
            payoutField.disabled = false;
            if (!payoutField.value && Number.isFinite(stake) && Number.isFinite(odds) && stake > 0 && odds > 1) {
                payoutField.value = (stake * odds).toFixed(2);
            }
        } else {
            payoutField.value = "";
            payoutField.disabled = true;
        }
    }

    resultField.addEventListener("change", updatePayoutState);
    stakeField.addEventListener("input", updatePayoutState);
    oddsField.addEventListener("input", updatePayoutState);
    updatePayoutState();
}

function setupDangerButtons() {
    var buttons = document.querySelectorAll("[data-confirm]");
    buttons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            var text = button.getAttribute("data-confirm");
            if (!text) {
                return;
            }
            var confirmed = window.confirm(text);
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-bet-form]").forEach(setupBetForm);
    setupDangerButtons();
});
