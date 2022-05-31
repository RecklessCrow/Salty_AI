import mysql.connector


class DatabaseHandler:
    def __init__(self):
        """
        Object to interact with the database
        """

        self.connection = None
        self.connection = mysql.connector.connect(
            host="localhost",
            user="saltybet",
            password="Dn9axQ`MCP^De<5x",
            database="saltybet"
        )
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
            values (%s, %s, %s)
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
            values (%s, %s, %s)
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
                where name = %s
                """,
                (character,)
            )

        self.cur.execute(
            """
            update characters
            set num_matches = num_matches + 1
            where name = %s
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

    def get_matchup_count(self, fighter_1, fighter_2):
        self.cur.execute(
            """
            select count(winner)
            from matches 
            where (red == %s and blue == %s) or (red == %s and blue == %s)
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
