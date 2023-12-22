import logging

from mongoengine import connect

from utils.config import config
from utils.db_models import MatchUp, Fighter, BetInfo
from datetime import datetime


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
        self.logger.info(f"Adding fighter {name}")
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
        self.logger.info(f"Getting or creating fighter {name}")
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
        self.logger.info(f"Getting token for {name}")
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
        self.logger.info("Getting number of tokens")
        return Fighter.objects.max_value('token')

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
        self.logger.info(f"Adding match {red} vs {blue} with winner {winner} and pots {red_pot} {blue_pot}")

        if isinstance(red, str):
            red = self.get_or_create_fighter(red)

        if isinstance(blue, str):
            blue = self.get_or_create_fighter(blue)

        match_up = MatchUp(red=red, blue=blue, winner=winner, red_pot=red_pot, blue_pot=blue_pot,
                           is_tournament=is_tournament, timestamp=timestamp)
        match_up.save()

        return match_up

    def add_bet(self, match_up: MatchUp, team_bet_on: str, amount_bet: int, model: str, red_confidence: float,
                blue_confidence: float) -> BetInfo:
        """
        Adds a bet to the database.

        Parameters
        ----------
        match_up : MatchUp
            The match up.
        team_bet_on : str
            The team bet on.
        amount_bet : int
            The amount bet.
        model : str
            The model used.
        red_confidence : float
            The confidence in the red team.
        blue_confidence : float
            The confidence in the blue team.

        Returns
        -------
        bet_info : BetInfo
        """
        self.logger.info(f"Adding bet on {match_up} for {team_bet_on} with amount {amount_bet} and model {model}")
        bet_info = BetInfo(match_up=match_up, team_bet_on=team_bet_on, amount_bet=amount_bet, model=model,
            red_confidence=red_confidence, blue_confidence=blue_confidence)

        bet_info.save()

        return bet_info

    def add_match_ups(self, match_ups: list[MatchUp]) -> None:
        """
        Adds a list of match ups to the database.

        Parameters
        ----------
        match_ups : list of MatchUp
            The match ups to add.
        """
        self.logger.info("Adding match ups")
        MatchUp.objects.insert(match_ups)

    def get_match_ups(self) -> list[MatchUp]:
        """
        Gets all match ups from the database.

        Returns
        -------
        match_ups : list of MatchUp
            A list of all match ups.
        """
        self.logger.info("Getting match ups")
        return MatchUp.objects()

    def get_fighters(self) -> list[Fighter]:
        """
        Gets all fighters from the database.

        Returns
        -------
        fighters : list of Fighter
            A list of all fighters.
        """
        self.logger.info("Getting fighters")
        return Fighter.objects()

    def delete_all_match_ups(self) -> None:
        """
        Deletes all match ups from the database.
        """
        self.logger.info("Deleting all match ups")
        MatchUp.drop_collection()

    def delete_all_fighters(self) -> None:
        """
        Deletes all fighters from the database.
        """
        # Reset the counter
        # from mongoengine.connection import _get_db
        # database = _get_db()
        # database["mongoengine.counter"].drop()

        self.logger.info("Deleting all fighters")
        Fighter.drop_collection()

    def nuke_database(self) -> None:
        """
        Deletes all data from the database.
        """
        self.logger.info("Nuking database")
        self.delete_all_fighters()
        self.delete_all_match_ups()


db = DBHandler()
