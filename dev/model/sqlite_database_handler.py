import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'database', 'salty.db')


class DatabaseHandler:
    def __init__(self):
        """
        Object to interact with the database
        """
        self.connection = None
        self.connection = sqlite3.connect(DATABASE_PATH)
        self.cur = self.connection.cursor()

    def __del__(self):
        if self.connection:
            self.cur.close()
            self.connection.close()

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
