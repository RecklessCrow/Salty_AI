from base import base_database_handler


class DatabaseHandler(base_database_handler.DatabaseHandler):
    def __init__(self, model_name: str, remake=False):
        """
        Object to interact with the database
        """
        super(DatabaseHandler, self).__init__()

        self.model_name = model_name

        if remake or not self.check_if_tables_exist():
            self.__create_tables()

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
            f"""
            create table {self.model_name}(
                match_id            integer     primary key,
                predicted_correctly boolean     not null,
                confidence          real        not null,
                end_balance         integer     not null
            );
            """
        )

        self.commit()

    def add_entry(self, predicted_correctly, confidence, end_balance):
        self.cur.execute(f"""
            insert into {self.model_name}(
                predicted_correctly, 
                confidence, 
                end_balance
            ) values (?, ?, ?)
        """, (predicted_correctly, confidence, end_balance))

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
