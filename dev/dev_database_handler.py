import os

import mysql.connector


class DatabaseHandler:
    def __init__(self):
        """
        Object to interact with the database
        """

        self.connection = None
        self.connection = mysql.connector.connect(
            host="overtimegaming.us.to",
            user="saltybet",
            password=self.__get_password(),
            database="saltybet"
        )
        self.cur = self.connection.cursor()

    def __del__(self):
        """
        Closes the connection to the database
        :return: None
        """

        if self.connection is not None:
            self.commit()
            self.connection.close()

    def commit(self):
        """
        Commits changes to the database
        :return: None
        """
        self.connection.commit()

    @staticmethod
    def __get_password():
        """
        Gets the password from password.txt
        :return:
        """
        path_to_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "database", "database_pass.txt")
        if not os.path.exists(path_to_file):
            exit("Database password file not found")

        with open(path_to_file, "r") as f:
            return f.read()

    def add_match(self, red: str, blue: str, winner: str):
        """
        Adds a match to the database
        :param red: The red team
        :param blue: The blue team
        :param winner: The winner of the match, either red or blue
        """

        assert winner in ["red", "blue"], "Winner must be 'red' or 'blue'"

        # Check if characters are in the database
        for character in red, blue:
            self.cur.execute("SELECT * FROM characters WHERE name = %s", (character,))
            if not self.cur.fetchone():
                self.cur.execute("INSERT INTO characters (name, num_wins, num_matches) VALUES (%s, 0, 0)", (character,))
                self.commit()

                # Increment the match count and winner count for the characters
                self.__increment_match_count(red, "red" == winner)
                self.__increment_match_count(blue, "blue" == winner)

        self.cur.execute("INSERT INTO matches (red, blue, winner) VALUES (%s, %s, %s)", (red, blue, winner))
        self.commit()

    def __increment_match_count(self, character: str, is_winner: bool):
        """
        Increment the match counter for a character
        :param character: Character to increment
        :param is_winner: If the character won the match, also increment their wins
        """
        if is_winner:
            self.cur.execute("UPDATE characters SET num_wins = num_wins + 1 WHERE name = %s", (character,))

        self.cur.execute("UPDATE characters SET num_matches = num_matches + 1 WHERE name = %s", (character,))
        self.commit()


class MatchDatabaseHandler(DatabaseHandler):
    def get_all_matches(self):
        """
        Returns all matches from the database.
        """
        self.cur.execute("SELECT red, blue, winner FROM matches")
        return self.cur.fetchall()

    def get_all_characters(self):
        """
        Returns all characters from the database.
        """
        self.cur.execute("SELECT * FROM characters")
        return self.cur.fetchall()


class ModelDatabaseHandler(DatabaseHandler):
    def __init__(self, model_name: str):
        """
        Initializes the database handler for the utils
        :param model_name: The name of the utils
        """

        super().__init__()
        self.model_name = model_name

    def get_balances(self):
        """
        Returns the balances at the end of each match
        :return:
        """
        self.cur.execute(f"SELECT balance FROM {self.model_name}")
        return self.cur.fetchall()

    def get_predicted_correctly(self):
        """
        Returns whether the utils predicted correctly for each match
        :return:
        """
        self.cur.execute(f"SELECT predicted_correctly FROM {self.model_name}")
        return self.cur.fetchall()

    def get_confidences(self):
        """
        Returns the confidence of the utils for each match
        :return:
        """
        self.cur.execute(f"SELECT confidence FROM {self.model_name}")
        return self.cur.fetchall()

    def get_predicted_correctly_and_confidences(self):
        """
        Returns the predicted and confidence for each match
        :return:
        """
        self.cur.execute(f"SELECT predicted_correctly, confidence FROM {self.model_name}")
        return self.cur.fetchall()
