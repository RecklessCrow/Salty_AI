const eventSource = new EventSource('/stream');

eventSource.addEventListener('update', ({data}) => {

    // Parse the data
    const {
        balance,
        red,
        red_odds,
        red_pot,
        blue,
        blue_odds,
        blue_pot,
        potential_payout,
        accuracy,
        confidence,
        bet,
        team_bet_on,
        is_tournament,
    } = JSON.parse(data);

    // Get the elements from the DOM
    const elements = {
        balance: document.getElementById('balance'),
        redTeam: document.getElementById('red-team'),
        redOdds: document.getElementById('red-odds'),
        redPot: document.getElementById('red-pot'),
        blueTeam: document.getElementById('blue-team'),
        blueOdds: document.getElementById('blue-odds'),
        bluePot: document.getElementById('blue-pot'),
        potentialPayout: document.getElementById('potential-payout'),
        accuracy: document.getElementById('accuracy'),
        confidence: document.getElementById('confidence'),
        bet: document.getElementById('bet'),
    };

    // Set the text of the elements
    const loading = 'Loading...';
    elements.balance.innerHTML = balance || loading;
    elements.redTeam.innerHTML = red || loading;
    elements.redOdds.innerHTML = red_odds || loading;
    elements.redPot.innerHTML = red_pot || loading;
    elements.blueTeam.innerHTML = blue || loading;
    elements.blueOdds.innerHTML = blue_odds || loading;
    elements.bluePot.innerHTML = blue_pot || loading;
    elements.potentialPayout.innerHTML = potential_payout || loading;
    elements.accuracy.innerHTML = accuracy || loading;
    elements.confidence.innerHTML = confidence || loading;

    // Set the color of the bet element based on the team being bet on
    elements.bet.innerHTML = bet;
    if (team_bet_on === 'red') {
        elements.bet.classList.remove('white-text');
        elements.bet.classList.add('red-text');
    } else if (team_bet_on === 'blue') {
        elements.bet.classList.remove('white-text');
        elements.bet.classList.add('blue-text');
    }

    // Set the color of balance based on whether it's a tournament or not
    elements.balance.classList.remove('green-text', 'purple-text');
    elements.potentialPayout.classList.remove('green-text', 'purple-text');
    if (is_tournament) {
        elements.balance.classList.add('purple-text');
        elements.potentialPayout.classList.add('purple-text');
    } else {
        elements.balance.classList.add('green-text');
        elements.potentialPayout.classList.add('green-text');
    }
});