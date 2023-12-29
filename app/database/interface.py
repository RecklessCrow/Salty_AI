import logging
from datetime import datetime

from mongoengine import connect

from database.models import MatchUp, Fighter
from utils.config import config

connect(host=str(config.DB_DSN))


class DBHandler:
    def __init__(self):
        self.logger = logging.getLogger("DBHandler")

    def add_fighter(self, name: str) -> None:
        """
        Adds a fighter to the database.

        Parameters
        ----------
        name : str
            The name of the fighter.

        Returns
        -------
        None
        """
        self.logger.debug(f"Adding fighter {name}")
        fighter = Fighter(name=name)
        fighter.save()

    def get_or_create_fighter(self, name) -> Fighter:
        """
        Gets a fighter from the database. If the fighter is not in the database, creates it.

        Parameters
        ----------
        name : str
            The name of the fighter.

        Returns
        -------
        fighter : Fighter
            The fighter object.
        """
        self.logger.debug(f"Getting or creating fighter {name}")
        fighter = Fighter.objects(name=name).first()
        if fighter is None:
            fighter = Fighter(name=name)
            fighter.save()
        return fighter

    def get_token_from_name(self, name: str) -> int or None:
        """
        Gets the token for a character. If the character is not in the database, returns None.

        Parameters
        ----------
        name : str
            The name of the character.

        Returns
        -------
        token : int or None
            The token for the character, or None if the character is not in the database.
        """
        self.logger.debug(f"Getting token for {name}")
        fighter = Fighter.objects(name=name).first()
        if fighter is None:
            return None
        return fighter.token

    def get_num_tokens(self) -> int:
        """
        Gets the number of tokens in the database.

        Returns
        -------
        num_tokens : int
            The number of tokens in the database.
        """
        self.logger.debug("Getting number of tokens")
        fighters = Fighter.objects()
        fighters = fighters.order_by("-token")
        return fighters[0].token + 1

    def add_match(self, red: Fighter or str, blue: Fighter or str, winner: str, red_pot: int = None,
                  blue_pot: int = None, is_tournament: bool = False, timestamp: datetime = None) -> MatchUp:
        """
        Adds a match to the database.

        Parameters
        ----------
        red : Fighter or str
            The red fighter.
        blue : Fighter or str
            The blue fighter.
        winner : str
            The winner of the match. Must be either "red" or "blue".
        red_pot : int
            The red pot.
        blue_pot : int
            The blue pot.
        is_tournament : bool
            Whether the match is a tournament match.
        timestamp : datetime
            The timestamp of the match.
        """
        self.logger.debug(f"Adding match {red} vs {blue} with winner {winner} and pots {red_pot} {blue_pot}")

        if isinstance(red, str):
            red = self.get_or_create_fighter(red)

        if isinstance(blue, str):
            blue = self.get_or_create_fighter(blue)

        match_up = MatchUp(red=red, blue=blue, winner=winner, red_pot=red_pot, blue_pot=blue_pot,
                           is_tournament=is_tournament, timestamp=timestamp)
        match_up.save()

        return match_up

    def add_match_ups(self, match_ups: list[MatchUp]) -> None:
        """
        Adds a list of match ups to the database.

        Parameters
        ----------
        match_ups : list of MatchUp
            The match ups to add.
        """
        self.logger.debug("Adding match ups")
        MatchUp.objects.insert(match_ups)

    def get_match_ups(self, num=None) -> list[MatchUp]:
        """
        Gets all match ups from the database.

        Returns
        -------
        match_ups : list of MatchUp
            A list of all match ups.
        """
        self.logger.debug("Getting match ups")

        if num is not None:
            return MatchUp.objects[:num]

        return MatchUp.objects()

    def get_training_data(self):
        self.logger.debug("Getting training data")

        matchups_info = []

        # Use MongoDB's aggregate framework to "join" MatchUp and Fighter documents
        pipeline = [
            {
                "$lookup": {
                    "from": "fighter",  # Name of the Fighter collection
                    "localField": "red",
                    "foreignField": "_id",
                    "as": "red_fighter"
                }
            },
            {
                "$lookup": {
                    "from": "fighter",
                    "localField": "blue",
                    "foreignField": "_id",
                    "as": "blue_fighter"
                }
            },
            {
                "$project": {
                    "red_id": "$red_fighter._id",
                    "blue_id": "$blue_fighter._id",
                    "winner": 1
                }
            }
        ]

        # Execute the aggregation pipeline
        cursor = MatchUp.objects.aggregate(*pipeline)

        # Iterate over the result cursor
        for result in cursor:
            try:
                red_id = result["red_id"][0]
                blue_id = result["blue_id"][0]
                winner = result["winner"]
            except IndexError:
                print(result)
                continue

            if winner == "n/a":
                continue

            winner = [1, 0] if winner == 'red' else [0, 1]

            matchups_info.append((red_id, blue_id, winner))

        return matchups_info

    def get_fighters(self) -> list[Fighter]:
        """
        Gets all fighters from the database.

        Returns
        -------
        fighters : list of Fighter
            A list of all fighters.
        """
        self.logger.debug("Getting fighters")
        return Fighter.objects()

    def delete_all_match_ups(self) -> None:
        """
        Deletes all match ups from the database.
        """
        self.logger.debug("Deleting all match ups")
        MatchUp.drop_collection()

    def delete_all_fighters(self) -> None:
        """
        Deletes all fighters from the database.
        """
        # Reset the counter
        # from mongoengine.connection import _get_db
        # database = _get_db()
        # database["mongoengine.counter"].drop()

        self.logger.debug("Deleting all fighters")
        Fighter.drop_collection()

    def get_matchup_odds(self, red, blue):
        self.logger.debug(f"Getting matchup odds for {red} vs {blue}")

        red = self.get_or_create_fighter(red)
        blue = self.get_or_create_fighter(blue)
        matchups = MatchUp.objects(red=red, blue=blue)

        red_pot = 0
        blue_pot = 0
        count = len(matchups)
        for matchup in matchups:
            if matchup.red_pot is None or matchup.blue_pot is None:
                count -= 1
                continue
            red_pot += matchup.red_pot
            blue_pot += matchup.blue_pot

        matchups = MatchUp.objects(red=blue, blue=red)
        count += len(matchups)
        for matchup in matchups:
            if matchup.red_pot is None or matchup.blue_pot is None:
                count -= 1
                continue
            red_pot += matchup.blue_pot
            blue_pot += matchup.red_pot

        if count == 0:
            self.logger.debug(f"No matchups found for {red} vs {blue}")
            return None, None

        # Average the pots and calculate the odds
        red_pot /= count
        blue_pot /= count

        # Odds should be a ratio of the potential payout to the amount bet
        if red_pot < blue_pot:
            red_odds = blue_pot / red_pot
            blue_odds = 1
        else:
            red_odds = 1
            blue_odds = red_pot / blue_pot

        return round(red_odds, 1), round(blue_odds, 1)

    def nuke_database(self) -> None:
        """
        Deletes all data from the database.
        """
        self.logger.debug("Nuking database")
        self.delete_all_fighters()
        self.delete_all_match_ups()


db = DBHandler()
