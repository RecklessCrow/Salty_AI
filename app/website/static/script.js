const storageKey = 'last-event-data';


eel.expose(updateMain);
function updateMain(data) {

    console.log('Received update event: ', data);

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
    } = data;

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

    // If the confidence is less than 0, set it to NaN
    if (confidence < 0) {
        elements.confidence.text('NaN');
    }

    // Save the last event data to localStorage
    localStorage.setItem(storageKey, data);
}

eel.expose(updateHistory);
function updateHistory(history_data) {
    console.log("Received history event:", history_data);
    const matchElement = build_match_history_element(history_data);

    // Prepend the new element to the beginning of the div
    const div = document.getElementById('match-history');
    // if (div.firstChild) {
    div.insertBefore(matchElement, div.firstChild);
    // } else {
    //     div.appendChild(matchElement);
    // }

    // Check if there are more than 10 elements in the div
    if (div.children.length > 10) {
        // If there are, remove the last element in the div
        div.removeChild(div.lastChild);
    }
}

// If there is last event data, use it to populate the website when it loads
$(document).ready(function () {
    // Retrieve the last event data from localStorage
    const lastEventData = localStorage.getItem(storageKey);
    if (lastEventData) {
        updateMain(lastEventData);
    }
});


function build_match_history_element(match_json) {
    const {
        red,
        blue,
        winner,
        payout,
    } = match_json;

    // Create the main container div
    const container = document.createElement('div');
    container.className = 'match-history-element';

    // Create the match-up div
    const matchUp = document.createElement('div');
    matchUp.className = 'match-history-match-up';

    // Create the left and right span elements for the match-up div
    const leftSpan = document.createElement('span');
    leftSpan.className = 'left red-text';
    leftSpan.textContent = 'Red';

    const middleSpan = document.createElement('span');
    middleSpan.className = 'white-text';
    middleSpan.textContent = 'VS';

    const rightSpan = document.createElement('span');
    rightSpan.className = 'right blue-text';
    rightSpan.textContent = 'Blue';

    // Append the left, middle, and right spans to the match-up div
    matchUp.appendChild(leftSpan);
    matchUp.appendChild(middleSpan);
    matchUp.appendChild(rightSpan);

    // Create the winner div
    const winnerDiv = document.createElement('div');
    winnerDiv.className = 'match-history-row';

    // Create the "Winner:" and winner span elements for the winner div
    const winnerLabel = document.createElement('span');
    winnerLabel.className = 'white-text match-left';
    winnerLabel.textContent = 'Winner:';

    const winnerName = document.createElement('span');
    if (winner === 'red') {
        winnerName.className = 'red-text match-right';
        winnerName.textContent = red;
    } else {
        winnerName.className = 'blue-text match-right';
        winnerName.textContent = blue;
    }

    // Append the winner label and winner name to the winner div
    winnerDiv.appendChild(winnerLabel);
    winnerDiv.appendChild(winnerName);

    // Create the payout div
    const payoutDiv = document.createElement('div');
    payoutDiv.className = 'match-history-row';

    // Create the "Payout:" and payout amount span elements for the payout div
    const payoutLabel = document.createElement('span');
    payoutLabel.className = 'white-text match-left';
    payoutLabel.textContent = 'Payout:';

    const payoutAmount = document.createElement('span');
    if (payout.includes('-')) {
        payoutAmount.className = 'red-text  match-right';
    } else {
        payoutAmount.className = 'green-text match-right';
    }

    payoutAmount.textContent = payout;

    // Append the payout label and payout amount to the payout div
    payoutDiv.appendChild(payoutLabel);
    payoutDiv.appendChild(payoutAmount);

    // Append the match-up, winner, and payout divs to the main container div
    container.appendChild(matchUp);
    container.appendChild(winnerDiv);
    container.appendChild(payoutDiv);

    return container;
}

