import os
import sqlite3
import zipfile

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from tqdm import tqdm

DB_FILE = os.path.join("../", "../", "database", "salty.db")


class DatabaseHandler:
    def __init__(self, model_name: str, remake=False):
        """
        Object to interact with the database
        """
        assert os.path.exists(DB_FILE)

        self.model_name = model_name
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
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (self.model_name,))
        return self.cur.fetchone() is not None

    def __create_tables(self):
        """
        Initializes the database if the database file does not exist
        """

        # make tables
        self.cur.execute("pragma foreign_keys = on;")
        self.cur.execute(
            """

            create table {}(
                match_id            integer     primary key,
                predicted_correctly boolean     not null,
                confidence          real        not null,
                end_balance         integer     not null
            );
            """.format(self.model_name)
        )

        self.commit()

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
            where (red == ? and blue == ?) or (red == ? and blue == ?)
            """,
            (fighter_1, fighter_2, fighter_2, fighter_1)
        )

        return self.cur.fetchone()[0]

    def add_entry(self, predicted_correctly, confidence, end_balance):
        self.cur.execute(f"""
            insert into {self.model_name}(
                predicted_correctly, 
                confidence, 
                end_balance
            ) values (?, ?, ?)
        """, (predicted_correctly, confidence, end_balance))
