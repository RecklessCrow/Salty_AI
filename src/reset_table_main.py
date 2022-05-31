import sys

from utils.database_handler import ModelDatabaseHandler


def reset_table():
    """
    Reset the table for a particular model.
    """
    if len(sys.argv) != 2:
        sys.exit(1)

    model_name = sys.argv[1]
    database = ModelDatabaseHandler(model_name)
    database.clear_history()


if __name__ == '__main__':
    reset_table()
