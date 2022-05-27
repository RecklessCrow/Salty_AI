import os
import sqlite3

import src.base_database_handler

DB_FILE = os.path.join("../", "../", "database", "salty.db")


class DatabaseHandler(src.base_database_handler.DatabaseHandler):
    def __init__(self, remake=False):
        """
        Object to interact with the database
        """

        super(DatabaseHandler, self).__init__(DB_FILE)

        if remake or not self.check_if_tables_exist():
            self.__create_tables()

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
