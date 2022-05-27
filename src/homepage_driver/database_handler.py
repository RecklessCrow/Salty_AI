import os
import sqlite3


DB_FILE = os.path.join("../", "../", "database", "salty.db")


class DatabaseHandler:
    def __init__(self, remake=False):
        """
        Object to interact with the database
        """

        assert os.path.exists(DB_FILE)

        self.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cur = self.connection.cursor()

        if remake or not self.check_if_tables_exist():
            self.__create_tables()

    def __del__(self):
        self.commit()
        self.cur.close()
        self.connection.close()

    def commit(self):
        """
        Commit changes to database file
        """
        self.connection.commit()

    def check_if_tables_exist(self):
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='homepage_matches';")
        return self.cur.fetchone() is not None

    def __create_tables(self):
        """
        Initializes the database if the database file does not exist
        """

        # make tables
        self.cur.execute("pragma foreign_keys = on;")
        self.cur.executescript(
            """
            
            create table homepage_matches(
                match_id        integer     primary key,
                red             text        not null,
                blue            text        not null,
                winner          text        not null,

                foreign key(red) references characters(name),
                foreign key(blue) references characters(name)
            );
            """
        )

        self.commit()

    def __add_character(self, name: str):
        """
        Add a character to the database
        :param name: Name of the character
        """
        self.cur.execute(
            """ 
            insert into characters (
                name,
                num_wins,
                num_matches
            )
            values (?, ?, ?)
            """,
            (name, 0, 0)
        )

    def __add_match(self, red: str, blue: str, winner: str):
        """
        Add a match to the database
        :param red: The red fighter
        :param blue: The blue fighter
        :param winner: Winning team of match, either "red" or "blue"
        """

        assert winner in ["red", "blue"]

        self.cur.execute(
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

    def __increment_match_count(self, character: str, is_winner: bool):
        """
        Increment the match counter for a character
        :param character: Character to increment
        :param is_winner: If the character won the match, also increment their wins
        """
        if is_winner:
            self.cur.execute(
                """
                update characters
                set num_wins = num_wins + 1
                where name = ?
                """,
                (character,)
            )

        self.cur.execute(
            """
            update characters
            set num_matches = num_matches + 1
            where name = ?
            """,
            (character,)
        )

    def match_over(self, red: str, blue: str, winner: str, commit=True):
        """
        Called when a match is finished. Will add the match to database as well as the characters if they were not
        already in the database
        :param red: The red fighter
        :param blue: The blue fighter
        :param winner: Winner of the match, either "red" or "blue"
        :param commit: Whether to commit this match to the database
        """

        assert winner in ["red", "blue"], "winner must be one of \"red\" or \"blue\""

        winner = winner.lower()
        winner_name = red if winner == "red" else blue
        for character in (red, blue):
            # Try to add character to the database
            try:
                self.__add_character(character)
            except sqlite3.IntegrityError:
                pass

            self.__increment_match_count(character, character == winner_name)

        self.__add_match(red, blue, winner)

        if commit:
            self.commit()

    def get_matchup_count(self, fighter_1, fighter_2):
        self.cur.execute(
            """
            select count(winner)
            from matches 
            where (red == ? and blue == ?) or (red == ? and blue == ?)
            """,
            (fighter_1, fighter_2, fighter_2, fighter_1)
        )

        return self.cur.fetchone()[0]
