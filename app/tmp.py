from utils.betting_module import betting_module

# logging.basicConfig(level=logging.DEBUG)
# Scarlet devil
amount, team = betting_module.get_wager("Mech zangief", "Chizuru kagura", 1_000_000, False)
print(amount, team)
