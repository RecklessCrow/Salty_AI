import os
import sqlite3
import zipfile

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from tqdm import tqdm

if not os.path.isdir("data"):
    os.mkdir("data")

ZIP_FILE = os.path.join("data", "match_data.zip")
MATCH_DATA = os.path.join("data", "match_data")
DB_FILE = os.path.join("data", "salty.db")


class DatabaseHandler:
    def __init__(self, remake=False, test_data_is_recent=False, seed=None):
        """
        Object to interact with the database
        """
        db_exists = os.path.exists(DB_FILE)

        self.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cur = self.connection.cursor()

        if not db_exists or remake:
            self.__create_database()

        self.encoder = OrdinalEncoder()
        self.encoder.fit(self.get_all_characters())

        self.x, self.y = self.__make_dataset()

        if test_data_is_recent:
            # take the n most recent matches from the database as opposed to a random split for a
            # potentially more representative test set
            test_matches = 10_000

            self.x_test, self.y_test = self.x[-test_matches:], self.y[-test_matches:]
            self.x_train, self.y_train = self.x[:-test_matches], self.y[:-test_matches]

            self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(self.x, self.y, test_size=0.1,
                                                                                  random_state=seed)
        else:
            # 70, 10, 20 % split
            self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(self.x, self.y, test_size=0.2,
                                                                                    random_state=seed)
            self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(self.x, self.y, test_size=0.125,
                                                                                  random_state=seed)

    def __del__(self):
        self.commit()
        self.cur.close()
        self.connection.close()

    def commit(self):
        """
        Commit changes to database file
        """
        self.connection.commit()

    def __create_database(self):
        """
        Initializes the database if the database file does not exist
        """
        # extract data from zip files
        with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall("data")

        # make tables
        self.cur.execute("pragma foreign_keys = on;")
        self.cur.executescript(
            """
            drop table if exists characters;
            drop table if exists matches;

            create table characters(
                name            text        primary key,
                num_wins        integer     not null,
                num_matches     integer     not null
            );

            create table matches(
                match_number    integer     primary key,
                red             text        not null,
                blue            text        not null,
                winner          text        not null,

                foreign key(red) references characters(name),
                foreign key(blue) references characters(name)
            );
            """
        )

        # Populate tables
        df = pd.read_csv(os.path.join(MATCH_DATA, "saltyRecordsM--2021-02-03-13.33.txt"))

        iter_obj = tqdm(df.iterrows(), desc="Populating Tables", total=len(df))
        for idx, (red, blue, winner,
                  strategy, prediction, tier,
                  mode, odds, time,
                  crowd_favor, illum_favor, date) in iter_obj:

            if "Team" in red or "Team" in blue:
                continue

            winner = "red" if winner == 0 else "blue"
            self.match_over(red, blue, winner, commit=False)

        df = pd.read_csv(os.path.join(MATCH_DATA, "match_data.csv")).dropna()

        iter_obj = tqdm(df.iterrows(), desc="Populating Tables", total=len(df))
        for idx, (_, match_id, red, blue, winner) in iter_obj:
            self.match_over(red, blue, winner, commit=False)

        self.commit()

    def add_character(self, name: str):
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

    def add_match(self, red: str, blue: str, winner: str):
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

    def increment_match_count(self, character: str, is_winner: bool):
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

        winner = winner.lower()
        winner_name = red if winner == "red" else blue
        for character in (red, blue):
            try:
                self.add_character(character)
            except sqlite3.IntegrityError:
                pass

            self.increment_match_count(character, character == winner_name)

        self.add_match(red, blue, winner)

        if commit:
            self.commit()

    def get_num_matches(self):
        """
        :return: The total number of matches in the database
        """
        self.cur.execute(
            """
            select max(match_number)
            from matches
            """
        )

        return self.cur.fetchone()[0]

    def get_all_matches(self):
        """
        :return: All the matches in the database as (red, blue, winner)
        """
        self.cur.execute(
            """
            select  red, blue, winner 
            from matches
            """
        )

        return self.cur.fetchall()

    def get_num_characters(self):
        """
        :return: The total number of characters in the database
        """
        self.cur.execute(
            """
            select count(name)
            from characters
            """
        )

        return self.cur.fetchone()[0]

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

    def get_matchup_info(self, red, blue):

        self.cur.execute(
            """
            select winner 
            from matches 
            where red == ? 
            and blue == ?
            """,
            (red, blue)
        )
        a = np.array(self.cur.fetchall()).reshape(-1, 1)

        self.cur.execute(
            """
            select winner 
            from matches 
            where red == ? 
            and blue == ?
            """,
            (blue, red)
        )
        b = self.cur.fetchall()

        if a and b:
            a = np.array(a).reshape(-1, 1)
            b = np.array(b).reshape(-1, 1)
            b = (b + 1) % 2
            return np.concatenate((a, b))
        elif a:
            return np.array(a).reshape(-1, 1)
        else:
            return np.array(b).reshape(-1, 1)

    def __make_dataset(self):
        """
        Formats the data for machine learning
        :return: x and y, the observation target pair
        """

        # todo if data becomes too large, add generator support
        matches = np.array(self.get_all_matches())

        self.encoder.fit(self.get_all_characters())
        red_vec = self.encoder.transform(np.array(matches[:, 0]).reshape(-1, 1)).flatten()
        blu_vec = self.encoder.transform(np.array(matches[:, 1]).reshape(-1, 1)).flatten()

        x = np.array(list(zip(red_vec, blu_vec)), dtype=int)
        y = np.array([[self.team_to_int(winner)] for winner in matches[:, -1]], dtype=int)

        return x, y

    def get_dataset(self):
        return self.x, self.y

    def get_train_data(self):
        return self.x_train, self.y_train

    def get_test_data(self):
        return self.x_test, self.y_test

    def get_val_data(self):
        return self.x_val, self.y_val

    def encode_character(self, x):
        """
        Transform character names to integer representations
        :param x: Characters to transform
        :return:
        """
        try:
            return self.encoder.transform(x)
        except ValueError:
            return np.array([0, 0])

    def decode_character(self, x):
        """
        Transform integer representations to character names
        :param x: integers to transform
        :return:
        """
        return self.encoder.inverse_transform(x)

    def get_matchup_info(self, red, blue):

        self.cur.execute(
            """
            select winner 
            from matches 
            where red == ? 
            and blue == ?
            """,
            (red, blue)
        )
        a = np.array(self.cur.fetchall()).reshape(-1, 1)

        self.cur.execute(
            """
            select winner 
            from matches 
            where red == ? 
            and blue == ?
            """,
            (blue, red)
        )
        b = self.cur.fetchall()
        if b:
            b = np.array(self.cur.fetchall()).reshape(-1, 1)
            b = (b + 1) % 2
            a = np.concatenate((a, b))

        return a

    @staticmethod
    def team_to_int(team):
        return int(team == "red")

    @staticmethod
    def int_to_team(number):
        return "red" if number else "blue"


if __name__ == '__main__':
    database = DatabaseHandler()
    x, y = database.get_dataset()

    print(x[-500:])
    print(database.decode_character(x.reshape(-1, 1)))
