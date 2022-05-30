import os
import sqlite3


class DatabaseHandler:
    DB_FILE = os.path.join("..", "database", "salty.db")

    def __init__(self, db_file=DB_FILE):
        """
        Object to interact with the database
        """

        self.connection = None
        if not os.path.exists(db_file):
            exit("Database file does not exist!")

        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cur = self.connection.cursor()

    def __del__(self):
        if self.connection:
            self.commit()
            self.cur.close()
            self.connection.close()


    def commit(self):
        """
        Commit changes to database file
        """
        self.connection.commit()

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

    def get_all_characters(self):
        """
        :return: The name of every character in the database
        """
        self.cur.execute(
            """
            select name
            from characters
            """
        )

        return self.cur.fetchall()

    def get_model_config_by_id(self, identifier):
        self.cur.execute(
            """
            select model_name, gambler_id, user, pass
            from model_configs
            where model_id = ?
            """,
            (identifier,)
        )

        return self.cur.fetchone()

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

    def get_all_matches(self, return_id=False):
        """
        :return: All the matches in the database as (red, blue, winner)
        """

        if return_id:
            self.cur.execute(
                """
                select  match_id, red, blue, winner 
                from matches
                """
            )
        else:
            self.cur.execute(
                """
                select  red, blue, winner 
                from matches
                """
            )

        return self.cur.fetchall()


DATABASE = DatabaseHandler()
