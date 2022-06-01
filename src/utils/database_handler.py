import os

import mysql.connector


class DatabaseHandler:
    def __init__(self):
        """
        Object to interact with the database
        """

        self.connection = None
        self.connection = mysql.connector.connect(
            host="10.0.0.2",
            user="saltybet",
            password=self.__get_password(),
            database="saltybet"
        )
        self.cur = self.connection.cursor(buffered=True)

    def __del__(self):
        """
        Closes the connection to the database
        :return: None
        """

        if self.connection:
            self.commit()
            self.connection.close()

    def commit(self):
        """
        Commit changes to the database
        """
        self.connection.commit()

    @staticmethod
    def __get_password():
        """
        Gets the password from password.txt
        :return:
        """
        path_to_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", "database",
                                    "database_pass.txt")

        if not os.path.exists(path_to_file):  # support for password being stored in .env file
            import dotenv
            dotenv.load_dotenv()
            password = os.getenv("DATABASE_PASSWORD")
            assert password is not None, "Password not found"
            return password

        with open(path_to_file, "r") as f:
            return f.read()


class MatchDatabaseHandler(DatabaseHandler):
    def __init__(self):
        """
        Database handler for Tables that deal with matches
        """
        super().__init__()

    def add_match(self, red: str, blue: str, winner: str):
        """
        Adds a match and its outcome to the database
        :param red: The red team
        :param blue: The blue team
        :param winner: The winner of the match, either red or blue
        """

        assert winner in ["red", "blue"], "Winner must be 'red' or 'blue'"

        self.__add_character_from_match(red, winner == "red")
        self.__add_character_from_match(blue, winner == "blue")
        self.cur.execute("INSERT INTO matches (red, blue, winner) VALUES (%s, %s, %s)", (red, blue, winner))
        self.commit()

        return self.cur.lastrowid

    def __add_character_from_match(self, character: str, is_winner: bool):
        """
        Add a character to the database if it doesn't already exist
        and update the character's win/loss count
        :param character:
        :return:
        """
        # Check if characters are in the database
        self.cur.execute("SELECT * FROM characters WHERE name = %s", (character,))
        if not self.cur.fetchone():
            self.cur.execute("INSERT INTO characters (name, num_wins, num_matches) VALUES (%s, 0, 0)", (character,))

        # Increment the match count and winner count for the characters
        if is_winner:
            self.cur.execute("UPDATE characters SET num_wins = num_wins + 1 WHERE name = %s", (character,))

        self.cur.execute("UPDATE characters SET num_matches = num_matches + 1 WHERE name = %s", (character,))
        self.commit()

    def get_all_characters(self):
        """
        Get all characters in the database
        :return: The name of every character in the database
        """
        self.cur.execute("SELECT name FROM characters")
        return self.cur.fetchall()

    def get_matchup_count(self, fighter_1, fighter_2):
        """
        Get the number of times a matchup has been played
        :param fighter_1: Name of the first fighter
        :param fighter_2: Name of the second fighter
        :return: The number of times fighter_1 has faced fighter_2
        """
        self.cur.execute(
            f"SELECT COUNT(*) FROM matches "
            "WHERE (red = %s AND blue = %s) OR (red = %s AND blue = %s)",
            (fighter_1, fighter_2, fighter_2, fighter_1)
        )
        return self.cur.fetchone()[0]

    def get_all_matches(self, return_id=False):
        """
        Get all matches in the database
        :param return_id: If True, return the id of the match as well
        :return: All the matches in the database as (red, blue, winner)
        """
        if return_id:
            self.cur.execute("SELECT * FROM matches")
        else:
            self.cur.execute("SELECT red, blue, winner FROM matches")

        return self.cur.fetchall()


class HomepageDatabaseHandler(MatchDatabaseHandler):
    def __init__(self):
        super().__init__()

    def add_match(self, red, blue, winner, red_odds, blue_odds, tier, red_pot, blue_pot, is_tournament, matchup_count):
        match_number = super().add_match(red, blue, winner)

        self.cur.execute(
            "INSERT INTO homepage (reference_number, red_odds, blue_odds, tier, red_pot, blue_pot, is_tournament, "
            "matchup_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (match_number, red_odds, blue_odds, tier, red_pot, blue_pot, is_tournament, matchup_count)
        )

        self.commit()


class ModelDatabaseHandler(DatabaseHandler):
    def __init__(self, model_name: str, remake=False):
        """
        Database handler for a utils database
        :param model_name: The name of the utils
        :param remake: If True, recreate the database
        """

        super().__init__()

        self.model_name = model_name

        if remake or not self.__check_if_table_exist():
            self.__create_table()

    def __check_if_table_exist(self):
        try:
            self.cur.execute(f"SELECT * FROM {self.model_name}")
            return True
        except mysql.connector.errors.ProgrammingError:
            return False

    def __create_table(self):
        """
        Creates the table for a models stats
        :return:
        """
        self.__drop_table()
        self.cur.execute(
            f"""
            CREATE TABLE {self.model_name}(
                match_id            INTEGER     AUTO_INCREMENT PRIMARY KEY,
                predicted_correctly BOOLEAN     NOT NULL,
                confidence          REAL        NOT NULL,
                end_balance         INTEGER     NOT NULL
            );
            """
        )
        self.commit()

    def add_match(self, predicted_correctly: bool, confidence: float, end_balance: int):
        """
        Add a predicted match to the utils's database
        :param predicted_correctly: True if the utils predicted the match correctly
        :param confidence: The confidence of the utils
        :param end_balance: The end balance of the utils
        :return:
        """
        self.cur.execute(
            f"INSERT INTO {self.model_name} (predicted_correctly, confidence, end_balance) VALUES (%s, %s, %s)",
            (predicted_correctly, confidence, end_balance)
        )
        self.commit()

    def get_balances(self):
        self.cur.execute(
            f"""
            select end_balance
            from {self.model_name}
            """
        )

        return self.cur.fetchall()

    def get_predicted_correctly(self):
        self.cur.execute(
            f"""
            select predicted_correctly
            from {self.model_name}
            """
        )

        return self.cur.fetchall()

    def get_confidences(self):
        self.cur.execute(
            f"""
            select confidence
            from {self.model_name}
            """
        )

        return self.cur.fetchall()

    def __drop_table(self):
        self.cur.execute(f"DROP TABLE IF EXISTS {self.model_name}")
        self.commit()

    def clear_history(self):
        self.__create_table()
