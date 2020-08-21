import random
import time

import numpy as np
from keras.models import save_model, load_model
import database_handler
import train_model


# from https://gist.github.com/EderSantana/c7222daa328f0e885093#file-qlearn-py-L157
class ExperienceReplay(object):
    def __init__(self, max_memory=100, discount=.9):
        self.max_memory = max_memory
        self.memory = list()
        self.discount = discount

    def remember(self, states, game_over):
        # memory[i] = [[state_t, action_t, reward_t, state_t+1], game_over?]
        self.memory.append([states, game_over])
        if len(self.memory) > self.max_memory:
            del self.memory[0]

    def get_batch(self, model, batch_size=10):
        len_memory = len(self.memory)
        num_actions = model.output_shape[-1]
        env_dim = self.memory[0][0][0].shape[1:]
        inputs = np.zeros(((min(len_memory, batch_size),) + env_dim))
        targets = np.zeros((inputs.shape[0], num_actions))
        for i, idx in enumerate(np.random.randint(0, len_memory,
                                                  size=inputs.shape[0])):
            state_t, action_t, reward_t, state_tp1 = self.memory[idx][0]
            game_over = self.memory[idx][1]

            inputs[i:i + 1] = state_t
            # There should be no target values for actions not taken.
            # Thou shalt not correct actions not taken #deep
            targets[i] = model.predict(state_t)[0]
            Q_sa = np.max(model.predict(state_tp1)[0])
            if game_over:  # if game_over is True
                targets[i, action_t] = reward_t
            else:
                # reward_t + gamma * max_a' Q(s', a')
                targets[i, action_t] = reward_t + self.discount * Q_sa
        return inputs, targets


class LiveEnvironment:

    def __init__(self):
        web_scraper.login()
        self.last_blue = ""
        self.last_red = ""
        self.beginning_balance = web_scraper.get_balance()

    def _update_state(self, action):
        web_scraper.simple_bet(action)

    def _get_reward(self):
        winner = None
        while winner is None:
            winner = web_scraper.get_bet_status()
            time.sleep(1)

        balance = web_scraper.get_balance()
        reward = balance - self.beginning_balance
        self.beginning_balance = balance

        if reward <= 0:
            return -1
        return 1

    def observe(self):
        while True:
            red, blue = web_scraper.get_red_blue()

            if self.last_red == red and self.last_blue == blue:
                time.sleep(1)
                continue

            self.last_blue = blue
            self.last_red = red
            break

        return web_scraper.get_more_stats()

    def act(self, action):
        self._update_state(action)

        reward = self._get_reward()
        game_over = reward == -1

        ob = self.observe()

        return ob, reward, game_over

    def reset(self):
        self.last_blue = ""
        self.last_red = ""
        self.beginning_balance = web_scraper.get_balance()


class Environment:

    def __init__(self):
        self.x, self.y = database_handler.select_all_matches()
        self.bad_counter = 0
        self.idx = 0

    def _update_state(self, action):
        pass

    def _get_reward(self, action):
        actual = np.argmax(np.array([self.y[self.idx]]))
        return 1 if action == actual else -1

    def observe(self):
        self.idx = random.randrange(len(self.x))
        ob2 = np.array([self.x[self.idx]])
        return ob2

    def act(self, action):
        self._update_state(action)
        ob = self.observe()

        reward = self._get_reward(action)
        self.bad_counter += 1 if reward == -1 else 0
        game_over = self.bad_counter == 5

        return ob, reward, game_over

    def reset(self):
        self.bad_counter = 0


if __name__ == "__main__":

    live = False
    if live:
        import web_scraper

        env = LiveEnvironment()
    else:
        env = Environment()

    # parameters
    epsilon = .1  # exploration
    num_actions = 2  # [Red, Blue]
    epoch = 1000
    max_memory = 500
    hidden_size = 100
    batch_size = 50
    grid_size = 10

    model = train_model.make_model()

    # Initialize experience replay object
    exp_replay = ExperienceReplay(max_memory=max_memory)

    # Train

    for e in range(epoch):
        win_cnt = 0
        loss = 0.0
        game_over = False
        # get initial input
        input_t = env.observe()

        while not game_over:
            input_tm1 = input_t
            # get next action
            if np.random.rand() <= epsilon:
                action = np.random.randint(0, num_actions, size=1)
            else:
                q = model.predict(input_tm1)
                action = np.argmax(q[0])

            # apply action, get rewards and new state
            input_t, reward, game_over = env.act(action)
            if reward >= 1:
                win_cnt += 1

            # store experience
            exp_replay.remember([input_tm1, action, reward, input_t], game_over)

            # adapt model
            inputs, targets = exp_replay.get_batch(model, batch_size=batch_size)

            loss += model.train_on_batch(inputs, targets)[0]

        env.reset()
        print(f"Epoch {e:03d}/999 | Loss {loss:.4f} | Win count {win_cnt}")

    save_model(model)
