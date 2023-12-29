from utils.betting_module import betting_module
from database.interface import db

# logging.basicConfig(level=logging.DEBUG)
# Scarlet devil
for match in db.get_match_ups(32):
    red, blue = betting_module.predict_winner(match.red.name, match.blue.name)
    print(f"{match.red} vs {match.blue}")
    print(f"Red: {red}")
    print(f"Blue: {blue}")
    print("-"*32)

