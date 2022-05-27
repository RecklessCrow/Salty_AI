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

    def __del__(self):
        self.commit()
        self.cur.close()
        self.connection.close()

    def commit(self):
        """
        Commit changes to database file
        """
        self.connection.commit()

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

DATABASE = DatabaseHandler()
