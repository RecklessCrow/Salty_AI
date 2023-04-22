from random import shuffle

import gym
import numpy as np
from gym import spaces
from sqlalchemy.orm import Session, aliased

import app.utils.database as db
from app.utils.helper_functions import predict_winner

INITIAL_BALANCE = 750


class SaltyBetEnv(gym.Env):
    def __init__(self):
        with Session(db.engine) as session:
            red = aliased(db.Character)
            blue = aliased(db.Character)

            match_data = session.query(
                red.name,
                blue.name,
                db.Match.winner,
                db.MatchMetadata.red_pot,
                db.MatchMetadata.blue_pot
            ).join(
                red, db.Match.red == red.name
            ).join(
                blue, db.Match.blue == blue.name
            ).filter(
                db.Match.id == db.MatchMetadata.match_id
            ).all()

            self.match_data = match_data
            self.match_idx = 0

            self.observation_space = spaces.Dict({
                'confidence': spaces.Box(low=0.5, high=1.0, shape=(1,), dtype='float32'),
                'balance': spaces.Box(low=INITIAL_BALANCE, high=float('inf'), shape=(1,), dtype='float32')
            })

            self.action_space = spaces.Box(low=0.01, high=1, shape=(1,), dtype='float32')

            self.balance = INITIAL_BALANCE

    def reset(self):
        self.match_idx = 0
        shuffle(self.match_data)
        self.balance = INITIAL_BALANCE
        red, blue, winner, red_pot, blue_pot = self.match_data[self.match_idx]
        conf, team = predict_winner(red, blue)
        return {
            'confidence': conf,
            'balance': self.balance
        }

    def step(self, action):
        bet = int(action * self.balance)
        red, blue, winner, red_pot, blue_pot = self.match_data[self.match_idx]
        conf, team = predict_winner(red, blue)
        balance_prior = self.balance

        if winner == team:
            ratio = max(red_pot, blue_pot) / min(red_pot, blue_pot)
            popular_team = 'red' if max(red_pot, blue_pot) == red_pot else 'blue'
            winnings = bet / ratio if team == popular_team else bet * ratio
            self.balance += np.ceil(winnings)
        else:
            self.balance -= bet

        reward = self.balance - balance_prior

        if self.balance < INITIAL_BALANCE:
            self.balance = INITIAL_BALANCE

        done = self.match_idx + 1 == len(self.match_data)
        self.match_idx += 1

        if not done:
            red, blue, winner, red_pot, blue_pot = self.match_data[self.match_idx]
            conf, team = predict_winner(red, blue)
        else:
            conf = 0.5

        observation = {
            "confidence": conf,
            "balance": self.balance
        }

        return observation, reward, done, {"reward": reward}


if __name__ == '__main__':
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3 import PPO, A2C
    from stable_baselines3.ppo import MultiInputPolicy
    from stable_baselines3.common.evaluation import evaluate_policy

    env = DummyVecEnv([lambda: SaltyBetEnv()])
    model = PPO(MultiInputPolicy, env, verbose=1, batch_size=2 ** 10)
    model.learn(total_timesteps=2**20)

    # Save the trained model
    model.save("betting_strategy_model")

    # Evaluate the policy for 10 episodes
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)

    print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
