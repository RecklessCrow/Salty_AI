import sys
from model_utils import database_handler


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    model_name = sys.argv[1]
    database = database_handler.DatabaseHandler(model_name)
    database.reset_table()
