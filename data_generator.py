import os

import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.preprocessing import Normalizer
from tqdm import tqdm, trange

character_info = pd.read_csv(os.path.join('data', 'character_information.csv'), index_col=False)
match_info = pd.read_csv(os.path.join('data', 'match_data.csv'), index_col=False)
match_info.dropna(axis=0, inplace=True)

le = preprocessing.LabelEncoder()
character_info['Author'].fillna(value=' ', inplace=True)
y = character_info['Author']
le.fit(y)

characters = []
character_ids = []
author_ids = []
character_wins = []
character_matches = []
author_wins = []
author_matches = []
hitbox_x = []
hitbox_y = []

authors = {}

preprocessor = Normalizer()


def generate_ratios():
    # Generate win loss ratios for lookup
    for i, (character_id, character_name, author, x, y) in tqdm(character_info.iterrows(),
                                                                desc='Generating win/loss for character lookup',
                                                                total=len(character_info)):

        author_id = le.transform([author])[0]

        character_win = 0
        character_match = 0

        if author_id not in authors:
            authors.update({author_id: (0, 0)})

        try:
            red_matches = match_info.query(f'(Red=="{character_name}")')
            character_match += len(red_matches)

            for match in red_matches.iterrows():
                if match[1][4] == 'Red':
                    character_win += 1

            blue_matches = match_info.query(f'(Blue=="{character_name}")')
            character_match += len(blue_matches)

            for match in blue_matches.iterrows():
                if match[1][4] == 'Blue':
                    character_win += 1

        except:
            print(character_name)

        new_author_wins = authors[author_id][0] + character_win
        new_author_matches = authors[author_id][1] + character_match

        authors[author_id] = (new_author_wins, new_author_matches)

        characters.append(character_name)
        character_ids.append(character_id)
        author_ids.append(author_id)
        character_wins.append(character_win)
        character_matches.append(character_match)
        author_wins.append(0)
        author_matches.append(0)
        hitbox_x.append(x)
        hitbox_y.append(y)

    # Validate author win/loss
    for i in trange(len(authors), desc='Validating Author win/loss'):
        my_id = author_ids[i]
        (author_win, author_match) = authors[my_id]
        author_wins[i] = author_win
        author_matches[i] = author_match

    character_lookup = pd.DataFrame({'character': characters,
                                     'character_id': character_ids,
                                     'character_wins': character_wins,
                                     'character_matches': character_matches,
                                     'author_id': author_ids,
                                     'author_wins': author_wins,
                                     'author_matches': author_matches,
                                     'hitbox_x': hitbox_x,
                                     'hitbox_y': hitbox_y}
                                    )

    character_lookup.set_index('character')

    character_lookup.to_csv(os.path.join('data', 'character_lookup.csv'))


def gen_data():
    # Generate data and label sets
    x_red = []
    x_blue = []
    y = []
    character_lookup = pd.read_csv(os.path.join('data', 'character_lookup.csv'))

    for i, (_, match_id, red, blue, winner) in tqdm(match_info.iterrows(),
                                                    desc=f'Generating data and labels.csv',
                                                    total=len(match_info)):

        a = character_lookup.loc[character_lookup['character'] == red].to_numpy()
        b = character_lookup.loc[character_lookup['character'] == blue].to_numpy()
        a = a[:, 2:].astype('float64')
        b = b[:, 2:].astype('float64')

        if not (np.any(np.isnan(a)) or np.any(np.isnan(b))):
            x_red.append(a[0])
            x_blue.append(b[0])
            y.append([winner])

    xr = np.array(x_red)
    xr = preprocessor.fit_transform(xr)
    df = pd.DataFrame(xr)
    df.to_csv(os.path.join('data', 'red_data.csv'))

    xb = np.array(x_blue)
    xb = preprocessor.transform(xb)
    df = pd.DataFrame(xb)
    df.to_csv(os.path.join('data', 'blue_data.csv'))

    y = np.array(y)
    df = pd.DataFrame(y)
    df.to_csv(os.path.join('data', 'labels.csv'))


if __name__ == '__main__':
    generate_ratios()
    gen_data()