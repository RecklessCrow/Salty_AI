import os
from sqlite3 import connect

db_file = os.path.join('data', 'salty_data.db')
connection = connect(db_file)
c = connection.cursor()


def drop_tables():
    c.executescript(
        """
        drop table if exists authors;
        drop table if exists characters;
        drop table if exists matches;
        """
    )


def create_tables():
    c.executescript(
        """
        create table if not exists authors(
            name text primary key,
            num_wins integer,
            num_matches integer
        );
        
        create table if not exists characters(
            name text primary key,
            author text,
            num_wins integer,
            num_matches integer,
            x integer,
            y integer,
            foreign key (author) references authors (name)
        );
        
        create table if not exists matches(
            match_num integer primary key,
            red text not null,
            blue text not null,
            winner bool not null,
            foreign key (red) references characters (name),
            foreign key (blue) references characters (name)
        );
        """
    )


def add_author(name, num_wins=None, num_matches=None):
    if num_wins is None:
        num_wins = 0

    if num_matches is None:
        num_matches = 1

    c.execute(
        """
        insert into authors (
            name,
            num_wins,
            num_matches
        )
        values (?, ?, ?)
        """,
        (name, num_wins, num_matches)
    )


def add_character(name, author=None, num_wins=None, num_matches=None, hitbox_x=None, hitbox_y=None):
    if num_wins is None:
        num_wins = 0

    if num_matches is None:
        num_matches = 1

    c.execute(
        """
        insert into characters (
            name,
            author,
            num_wins,
            num_matches,
            x,
            y
        )
        values (?, ?, ?, ?, ?, ?)
        """,
        (name, author, num_wins, num_matches, hitbox_x, hitbox_y)
    )


def add_match(red, blue, winner):
    c.execute(
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


def select_author(author):
    c.execute(
        """
        select *
        from authors
        where name = ?
        """,
        (author,)
    )

    authors = c.fetchall()

    if not authors:
        add_author(author)
        return select_author(author)

    return authors


def select_character(character):
    # todo use join to get author info
    c.execute(
        """
        select characters.name, characters.num_wins, characters.num_matches, 
        characters.author, authors.num_wins, authors.num_matches, characters.x, characters.y
        from characters
        left join authors
        on characters.author = authors.name
        where characters.name = ?
        """,
        (character,)
    )

    characters = c.fetchall()

    if not characters:
        add_character(character)
        return select_character(character)

    return characters


def select_matches(player_1, player_2):
    c.execute(
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

    matches = c.fetchall()

    return matches


if __name__ == '__main__':
    drop_tables()
    create_tables()
    au = 'author'
    au1 = 'author1'
    c1 = 'char_1'
    c2 = 'char_2'
    c3 = 'char_3'
    add_author(au)
    add_character(c1, au)
    add_character(c2)
    add_match(c1, c2, False)
    add_match(c2, c1, True)
    print(select_author(au))
    print(select_author(au1))
    print(select_character(c1))
    print(select_character(c2))
    print(select_character(c3))
    print(select_matches(c1, c2))
