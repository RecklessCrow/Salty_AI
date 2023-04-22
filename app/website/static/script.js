const eventSource = new EventSource('/stream');

eventSource.addEventListener('update', (event) => {
    const data = JSON.parse(event.data);  // Parse the data as JSON
    document.getElementById('balance').innerHTML = data.balance;
    document.getElementById('red-team').innerHTML = data.red;
    document.getElementById('red-odds').innerHTML = data.red_odds;
    document.getElementById('red-pot').innerHTML = data.red_pot;
    document.getElementById('blue-team').innerHTML = data.blue;
    document.getElementById('blue-odds').innerHTML = data.blue_odds;
    document.getElementById('blue-pot').innerHTML = data.blue_pot;
    document.getElementById('potential-payout').innerHTML = data.potential_payout;
    document.getElementById('accuracy').innerHTML = data.accuracy;

    // Set the color of the bet element based on the team being bet on
    document.getElementById('bet').innerHTML = data.bet;
    if (data.team_bet_on === 'red') {
        document.getElementById('bet').classList.remove('white-text');
        document.getElementById('bet').classList.add('red-text');
    } else if (data.team_bet_on === 'blue') {
        document.getElementById('bet').classList.remove('white-text');
        document.getElementById('bet').classList.add('blue-text');
    }

    // Set the color of balance based on whether it's a tournament or not
    if (data.is_tournament) {
        document.getElementById('balance').classList.remove('green-text');
        document.getElementById('balance').classList.add('purple-text');
        document.getElementById('potential-payout').classList.remove('green-text');
        document.getElementById('potential-payout').classList.add('purple-text');
    } else {
        document.getElementById('balance').classList.remove('purple-text');
        document.getElementById('balance').classList.add('green-text');
        document.getElementById('potential-payout').classList.remove('purple-text');
        document.getElementById('potential-payout').classList.add('green-text');
    }

})