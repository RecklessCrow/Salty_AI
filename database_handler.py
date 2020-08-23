import os
import sqlite3
from sqlite3 import connect

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from tqdm import tqdm

db_file = os.path.join('data', 'salty.db')
connection = connect(db_file, check_same_thread=False)
cur = connection.cursor()

imp = SimpleImputer(missing_values=None, strategy='constant', fill_value=-1)
label_encoder = OneHotEncoder()
label_encoder.fit([['red'], ['blue']])


def drop_tables():
    cur.executescript(
        """
        drop table if exists authors;
        drop table if exists characters;
        drop table if exists matches;
        """
    )


def create_tables():
    cur.executescript(
        """
        pragma foreign_keys = on;
        create table if not exists characters(
            name text primary key,
            num_wins integer,
            num_matches integer
        );
        
        create table if not exists matches(
            match_num integer primary key,
            red text not null,
            blue text not null,
            winner bool not null,
            foreign key(red) references characters(name),
            foreign key(blue) references characters(name)
        );
        """
    )


def add_character(name, num_wins=0, num_matches=1):
    cur.execute(
        """
        insert into characters (
            name,
            num_wins,
            num_matches
        )
        values (?, ?, ?)
        """,
        (name, num_wins, num_matches)
    )


def add_match(red, blue, winner):
    increment_character_match_history(red, (winner == 'red'))
    increment_character_match_history(blue, (winner == 'blue'))

    cur.execute(
        """
        insert into matches(
            red,
            blue,
            winner
        )
        values (?, ?, ?)
        """,
        (red, blue, winner)
    )


def increment_character_match_history(name, winner):

    try:
        add_character(name)
    except sqlite3.IntegrityError:
        pass

    if winner:
        cur.execute(
            '''
            update characters
            set num_wins = num_wins + 1
            where name = ?
            ;
            ''',
            (name,)
        )

    cur.execute(
        '''
        update characters
        set num_matches = num_matches + 1
        where name = ?
        ;
        ''',
        (name,)
    )


def format_match_output(matchup):
    global imp

    if not isinstance(matchup, list):
        matchup = list(matchup)

    x = np.array([match[:-1] for match in matchup])
    # try:
    #     x = imp.transform(x)
    # except NotFittedError:
    #     x = imp.fit_transform(x)

    x = x.reshape((-1, 2, 2)).astype('float64')

    y = [[winner[-1]] for winner in matchup]
    y = label_encoder.transform(y).toarray()

    return x, y


def select_all_matches():
    cur.execute(
        f"""
        select  r.num_wins * 100.0 / r.num_matches,  r.num_matches,
                b.num_wins * 100.0  / b.num_matches,  b.num_matches,
                winner
        from characters as r
        inner join matches
        on r.name = matches.red
        inner join characters as b
        on b.name = matches.blue
        """
    )

    matchup = cur.fetchall()

    return format_match_output(matchup)


def select_num_matches(num_matches):
    cur.execute(
        f"""
        select  r.num_wins * 100.0 / r.num_matches,  r.num_matches,
                b.num_wins * 100.0  / b.num_matches,  b.num_matches,
                winner
        from characters as r
        inner join matches
        on r.name = matches.red
        inner join characters as b 
        on b.name = matches.blue
        """
    )

    matchup = cur.fetchmany(num_matches)

    return format_match_output(matchup)


def create_database(drop=False):
    character_info = pd.read_csv(os.path.join('data', 'character_information.csv'))
    match_info = pd.read_csv(os.path.join('data', 'match_data.csv'))
    match_info.dropna(axis=0, inplace=True)

    if drop:
        drop_tables()

    create_tables()

    # for i, (char_id, char_name, char_author, hit_x, hit_y) in tqdm(character_info.iterrows(),
    #                                                                desc='Populating characters',
    #                                                                total=len(character_info)):
    #
    #     try:
    #         add_character(char_name)
    #     except sqlite3.IntegrityError:
    #         pass

    for i, (_, __, red, blue, winner) in tqdm(match_info.iterrows(),
                                              desc='Populating Matches',
                                              total=len(match_info)):
        winner = winner.lower()

        add_match(red, blue, winner)


if __name__ == '__main__':
    create_database(True)
    connection.commit()
    print(select_all_matches())
