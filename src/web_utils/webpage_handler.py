import os
from collections import deque

import numpy as np
import plotly.express as px
import plotly.io as pio
from web_utils.html_builder import *


class WebPageHandler:
    def __init__(self, model_name, balance_history, win_history):

        self.model_name = model_name
        self.box_deque = deque(maxlen=7)

        win_history = np.array(win_history).flatten()
        self.num_of_matches = len(win_history)
        self.accuracy = np.sum(win_history) / len(win_history)

        balance_history = np.array(balance_history).flatten()
        self.balance_deque = deque(balance_history, maxlen=1000)
        self.current_match_info = ''

        self.generate_html_page()

    def update_page(self, match_confidence, team_prediction,
                    red_name, blue_name, bet_amount, odds=None, winner=None, end_balance=None):

        if winner:
            # Payout
            if team_prediction == 'red':
                award_amount = bet_amount * odds[1]
                award_amount = award_amount / odds[0]
            else:
                award_amount = bet_amount * odds[0]
                award_amount = award_amount / odds[1]

            predicted_correct = team_prediction == winner
            balance_diff = award_amount if predicted_correct else -bet_amount

            box = create_feed_box(team_prediction, predicted_correct, match_confidence, balance_diff, odds, red_name, blue_name)
            self.box_deque.append(box)
            self.num_of_matches += 1
            self.accuracy = ((self.accuracy * (self.num_of_matches - 1)) +
                             (1 if predicted_correct else 0)) / self.num_of_matches
            self.balance_deque.append(end_balance)



        elif odds:
            # Betting Locked
            if team_prediction == 'red':
                award_amount = bet_amount * odds[1]
                award_amount = award_amount / odds[0]
            else:
                award_amount = bet_amount * odds[0]
                award_amount = award_amount / odds[1]

            self.current_match_info = update_current_match(match_confidence, team_prediction,
                                                      red_name, blue_name, odds, award_amount, bet_amount)
        else:
            # Betting Open
            self.current_match_info = create_current_match(match_confidence, team_prediction,
                                                           red_name, blue_name, bet_amount)

        self.generate_html_page()

    def generate_html_page(self):
        balance = 0
        if len(list(self.balance_deque)):
            balance = list(self.balance_deque)[-1]
        feed_boxes = ''.join(reversed(list(self.box_deque)))
        base = base_html_page(feed_boxes, self.model_name, balance, self.current_match_info)
        p1, p2 = self.generate_graphs()

        path = os.path.join(os.getcwd(), self.model_name)
        if not os.path.exists(path):
            os.mkdir(path)

        with open(os.path.join(path, f'{self.model_name}.html'), 'w') as f:
            f.write(base)

        with open(os.path.join(path, 'plot1.html'), 'w') as f:
            f.write(p1)

        with open(os.path.join(path, 'plot2.html'), 'w') as f:
            f.write(p2)

        return

    def generate_graphs(self):
        data = list(self.balance_deque)
        if len(data) < 1:
            return "", ""

        labels = {'x': '# of Matches', 'y': '$$$'}
        scatter = px.line(x=list(range(len(data))),
                          y=data,
                          title="Balance History",
                          template='plotly_dark',
                          labels=labels)

        labels = ['Incorrect', 'Correct']
        values = [1 - self.accuracy, self.accuracy]

        pie = px.pie(labels=labels, values=values, hole=.3, title='model Accuracy', template='plotly_dark')

        scatter = pio.to_html(scatter, full_html=False)
        pie = pio.to_html(pie, full_html=False)

        return scatter, pie
