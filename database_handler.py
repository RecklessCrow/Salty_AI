import os
import sqlite3
from sqlite3 import connect

import pandas as pd
from tqdm import tqdm

db_file = os.path.join('data', 'salty.db')
connection = connect(db_file, check_same_thread=False)
cur = connection.cursor()


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
        
        create table if not exists authors(
            name text primary key,
            id int not null,
            num_wins integer,
            num_matches integer
        );
        
        create table if not exists characters(
            name text primary key,
            id int not null,
            author text,
            num_wins integer,
            num_matches integer,
            x integer,
            y integer,
            foreign key(author) references authors(name)
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


def add_author(name, my_id=None, num_wins=None, num_matches=None):
    if my_id is None:
        my_id = get_next_author_id()

    if num_wins is None:
        num_wins = 0

    if num_matches is None:
        num_matches = 0

    cur.execute(
        """
        insert into authors (
            name,
            id,
            num_wins,
            num_matches
        )
        values (?, ?, ?, ?)
        """,
        (name, my_id, num_wins, num_matches)
    )


def add_character(name, my_id=None, author=None, num_wins=None, num_matches=None, hitbox_x=None, hitbox_y=None):
    if my_id is None:
        my_id = get_next_character_id()

    if num_wins is None:
        num_wins = 0

    if num_matches is None:
        num_matches = 0

    cur.execute(
        """
        insert into characters (
            name,
            id,
            author,
            num_wins,
            num_matches,
            x,
            y
        )
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, my_id, author, num_wins, num_matches, hitbox_x, hitbox_y)
    )


def add_match(red, blue, winner):
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

    def select_char_info(name):
        cur.execute(f'''
            select characters.name, authors.name
            from characters
            left join authors
            on characters.author = authors.name
            where characters.name = ?
        ''', (name,))

        return cur.fetchone()

    red_info = select_char_info(red)
    blue_info = select_char_info(blue)
    if red_info[1] is not None:
        red_author = select_author(red_info[1])[0]
        update_match_info('authors', red_author, not winner)
    if blue_info[1] is not None:
        blue_author = select_author(blue_info[1])[0]
        update_match_info('authors', blue_author, winner)
    update_match_info('characters', red, not winner)
    update_match_info('characters', blue, winner)


def select_author(author):
    cur.execute(
        """
        select *
        from authors
        where name = ?
        """,
        (author,)
    )

    authors = cur.fetchone()

    return authors


def select_character(character):
    cur.execute(
        """
        select characters.id, characters.num_wins, characters.num_matches, 
        authors.id, authors.num_wins, authors.num_matches, characters.x, characters.y
        from characters
        left join authors
        on characters.author = authors.name
        where characters.name = ?
        """,
        (character,)
    )

    characters = cur.fetchone()

    if not characters:
        add_character(character)
        return select_character(character)

    return characters


def select_matches(player_1, player_2):
    cur.execute(
        """
        select *
        from matches
        where red = ?
        and blue = ?
        or red = ?
        and blue = ?
        """,
        (player_1, player_2, player_2, player_1)
    )

    matches = cur.fetchall()

    return matches


def select_all(table):
    cur.execute(
        f"""
        select *
        from {table}
        """
    )

    return cur.fetchall()


def update_match_info(table, name, win):
    if win:
        cur.execute(
            f"""
            update {table}
            set num_wins = num_wins + 1
            where name = ?
            """,
            (name,)
        )

    cur.execute(
        f"""
        update {table}
        set num_matches = num_matches + 1
        where name = ?
        """,
        (name,)
    )


def get_next_author_id():
    cur.execute(
        """
        select max(id)
        from authors
        """
    )

    next_id = cur.fetchone()[0]

    if next_id is None:
        return 0

    return next_id + 1


def get_next_character_id():
    cur.execute(
        """
        select max(id)
        from characters
        """
    )

    next_id = cur.fetchone()[0]

    if next_id is None:
        return 0

    return next_id + 1


def create_database(drop=False):

    character_info = pd.read_csv(os.path.join('data', 'character_information.csv'))
    match_info = pd.read_csv(os.path.join('data', 'match_data.csv'))
    match_info.dropna(axis=0, inplace=True)

    if drop:
        drop_tables()
    create_tables()

    for i, (char_id, char_name, char_author, hit_x, hit_y) in tqdm(character_info.iterrows(),
                                                                   desc='Populating characters and authors',
                                                                   total=len(character_info)):
        try:
            add_author(char_author)
        except sqlite3.IntegrityError:
            pass

        try:
            add_character(char_name, my_id=char_id, author=char_author, hitbox_x=hit_x, hitbox_y=hit_y)
        except sqlite3.IntegrityError:
            pass

    for i, (_, __, red, blue, winner) in tqdm(match_info.iterrows(),
                                              desc='Populating Matches',
                                              total=len(match_info)):
        if winner == 'Red':
            winner = 0
        else:
            winner = 1
        add_match(red, blue, winner)


def select_rand_match(limit):
    cur.execute(
        f"""
        select  r.id, r.num_wins, r.num_matches, ra.id, ra.num_wins, ra.num_matches, r.x, r.y,
                b.id, b.num_wins, b.num_matches, ba.id, ba.num_wins, ba.num_matches, b.x, b.y,
                winner
        from characters as r
        inner join matches
        on r.name = matches.red
        inner join characters as b
        on b.name = matches.blue
        left join authors as ra
        on ra.name = r.author
        left join authors as ba
        on ba.name = b.author
        order by random()
        limit {limit}
        """
    )

    char = cur.fetchall()

    return char


def select_all_matches():
    cur.execute(
        f"""
        select  r.id, r.num_wins, r.num_matches, ra.id, ra.num_wins, ra.num_matches, r.x, r.y,
                b.id, b.num_wins, b.num_matches, ba.id, ba.num_wins, ba.num_matches, b.x, b.y,
                winner
        from characters as r
        inner join matches
        on r.name = matches.red
        inner join characters as b
        on b.name = matches.blue
        left join authors as ra
        on ra.name = r.author
        left join authors as ba
        on ba.name = b.author
        """
    )

    char = cur.fetchall()

    return char


if __name__ == '__main__':
    create_database(True)
    connection.commit()
