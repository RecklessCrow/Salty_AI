$(document).ready(function () {
    getData();
    setInterval(getData, 2500);
});

function getData() {
    $.getJSON('/data', function (data) {
        $('#balance').html(data.balance ? data.balance : "Loading...");
        $('#red-team').html(data.red ? data.red : "Loading...");
        $('#red-odds').html(data.red_odds ? data.red_odds : "Loading...");
        $('#red-pot').html(data.red_pot ? data.red_pot : "Loading...");
        $('#blue-team').html(data.blue ? data.blue : "Loading...");
        $('#blue-odds').html(data.blue_odds ? data.blue_odds : "Loading...");
        $('#blue-pot').html(data.blue_pot ? data.blue_pot : "Loading...");
        $('#potential-payout').html(data.potential_payout ? data.potential_payout : "Loading...");
        $('#accuracy').html(data.accuracy ? data.accuracy : "Loading...");
        $('#confidence').html(data.confidence ? data.confidence : "Loading...");

        // Set the color of the bet element based on the team being bet on
        $('#bet').html(data.bet ? data.bet : "Loading...");
        if (data.team_bet_on === 'red') {
            $('#bet').removeClass('white-text').addClass('red-text');
        } else if (data.team_bet_on === 'blue') {
            $('#bet').removeClass('white-text').addClass('blue-text');
        }

        // Set the color of balance based on whether it's a tournament or not
        if (data.is_tournament) {
            $('#balance').removeClass('green-text').addClass('purple-text');
            $('#potential-payout').removeClass('green-text').addClass('purple-text');
        } else {
            $('#balance').removeClass('purple-text').addClass('green-text');
            $('#potential-payout').removeClass('purple-text').addClass('green-text');
        }
    });
}
