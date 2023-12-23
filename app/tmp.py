from models.data import MatchDataset

from tqdm import tqdm
from database.driver import db

data = db.get_match_ups(128)
data_list = []
for idx in range(len(data)):
    winner = [1, 0] if data[idx].winner == 'red' else [0, 1]
    x = [data[idx].red.token, data[idx].blue.token, winner]
    data_list.append(x)

dataset = MatchDataset(tqdm(data_list, desc="Loading data", total=len(data)))
# print(len(dataset))
dataset[0]
dataset[:32]
