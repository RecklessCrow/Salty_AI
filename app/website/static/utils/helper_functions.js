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
    leftSpan.textContent = red;

    const middleSpan = document.createElement('span');
    middleSpan.className = 'white-text';
    middleSpan.textContent = 'VS';

    const rightSpan = document.createElement('span');
    rightSpan.className = 'right blue-text';
    rightSpan.textContent = blue;

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
        payoutAmount.textContent = payout;
    } else {
        payoutAmount.className = 'green-text match-right';
        // Add a + sign to the payout amount if it's positive
        payoutAmount.textContent = '+' + payout;
    }

    // Append the payout label and payout amount to the payout div
    payoutDiv.appendChild(payoutLabel);
    payoutDiv.appendChild(payoutAmount);

    // Append the match-up, winner, and payout divs to the main container div
    container.appendChild(matchUp);
    container.appendChild(winnerDiv);
    container.appendChild(payoutDiv);

    return container;
}