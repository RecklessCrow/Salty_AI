const eventSource = new EventSource('/stream');
const storageKey = 'last-event-data';


eventSource.addEventListener('update', ({data}) => {
    console.log(data);

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

    // Get the elements from the DOM using jQuery
    const elements = {
        balance: $('#balance'),
        redTeam: $('#red-team'),
        redOdds: $('#red-odds'),
        redPot: $('#red-pot'),
        blueTeam: $('#blue-team'),
        blueOdds: $('#blue-odds'),
        bluePot: $('#blue-pot'),
        potentialPayout: $('#potential-payout'),
        accuracy: $('#accuracy'),
        confidence: $('#confidence'),
        bet: $('#bet'),
    };

    // Set the text of the elements
    const loading = 'Loading...';
    elements.balance.text(balance || loading);
    elements.redTeam.text(red || loading);
    elements.redOdds.text(red_odds || loading);
    elements.redPot.text(red_pot || loading);
    elements.blueTeam.text(blue || loading);
    elements.blueOdds.text(blue_odds || loading);
    elements.bluePot.text(blue_pot || loading);
    elements.potentialPayout.text(potential_payout || loading);
    elements.accuracy.text(accuracy || loading);
    elements.confidence.text(confidence || loading);

    // Set the color of the bet element based on the team being bet on
    elements.bet.text(bet);
    if (team_bet_on === 'red') {
        elements.bet.removeClass('white-text');
        elements.bet.addClass('red-text');
    } else if (team_bet_on === 'blue') {
        elements.bet.removeClass('white-text');
        elements.bet.addClass('blue-text');
    }

    // Set the color of balance based on whether it's a tournament or not
    elements.balance.removeClass('green-text purple-text');
    elements.potentialPayout.removeClass('green-text purple-text');
    if (is_tournament) {
        elements.balance.addClass('purple-text');
        elements.potentialPayout.addClass('purple-text');
    } else {
        elements.balance.addClass('green-text');
        elements.potentialPayout.addClass('green-text');
    }

    // Save the last event data to localStorage
    localStorage.setItem(storageKey, data);
});

// If there is last event data, use it to populate the website when it loads
$(document).ready(function () {
    // Retrieve the last event data from localStorage
    const lastEventData = JSON.parse(localStorage.getItem(storageKey));
    if (lastEventData) {
        eventSource.dispatchEvent(new MessageEvent('update', {data: JSON.stringify(lastEventData)}));
    }
});
