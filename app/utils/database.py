import logging
import time

import sqlalchemy
from sqlalchemy import ForeignKey, select, Identity
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, Session

from app.utils.settings import settings


class Base(DeclarativeBase):
    pass


class Character(Base):
    """
    SQL table for characters.

    Attributes
    ----------
    id : int
        ID of the row.
    name : str
        Name of the character.
    num_wins : int
        Number of wins the character has.
    num_matches : int
        Number of matches the character has been in.
    """
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(Identity())
    name: Mapped[str] = mapped_column(primary_key=True)
    num_wins: Mapped[int] = mapped_column(nullable=False)
    num_matches: Mapped[int] = mapped_column(nullable=False)


class Match(Base):
    """
    SQL table for matches.

    Attributes
    ----------
    id : int
        ID of the row.
    red : str
        Name of the red team.
    blue : str
        Name of the blue team.
    winner : str
        Name of the winning team.
    """
    __tablename__ = 'matches'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    red: Mapped[str] = mapped_column(ForeignKey("characters.name"), nullable=False)
    blue: Mapped[str] = mapped_column(ForeignKey("characters.name"), nullable=False)
    winner: Mapped[str] = mapped_column(nullable=False)

    def __str__(self):
        return f"{self.red} vs. {self.blue}: {self.winner.capitalize()} wins!"


class MatchMetadata(Base):
    """
    SQL table for metadata on matches. Not all matches have this information recorded, thus the need for a
    separate table.

    Attributes
    ----------
    id : int
        ID of the row.
    match_id : int
        ID of the mapped match.
    red_pot : int
        Amount of money in the red team's pot.
    blue_pot : int
        Amount of money in the blue team's pot.
    """
    __tablename__ = 'match_metadata'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    red_pot: Mapped[int] = mapped_column(nullable=False)
    blue_pot: Mapped[int] = mapped_column(nullable=False)


class ModelMetadata(Base):
    """
    SQL table for metadata on matches. Not all matches have this information recorded, thus the need for a
    separate table.

    Attributes
    ----------
    id : int
        ID of the row.
    model_id : str
        ID of the model that made the prediction.
    match_id : int
        ID of the mapped match.
    confidence : float
        Confidence of the prediction.
    bet_on : str
        Team the model bet on.
    amount_bet : float
        Amount of money the model bet.
    payout : int
        Amount of money the model won.
    """
    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    bet_on: Mapped[str] = mapped_column(nullable=False)
    amount_bet: Mapped[float] = mapped_column(nullable=False)
    payout: Mapped[int] = mapped_column(nullable=False)


def update_character(session: Session, name: str, is_winner: bool):
    try:
        character = session.query(Character).filter_by(name=name).one()
        character.num_wins += int(is_winner)
        character.num_matches += 1
    except NoResultFound:
        # Character does not exist in database, so add it
        character = Character(name=name, num_wins=int(is_winner), num_matches=1)
        session.add(character)


def add_match(red, blue, winner, pots=None, commit=True, num_retries=3):
    """
    Add a match to the database.

    Parameters
    ----------
    red : str
        Name of the red character.
    blue : str
        Name of the blue character.
    winner : str
        Name of the winning character.
    pots : tuple[int, int], default=None
        Tuple of (red_pot, blue_pot) for the match.
    commit : bool, default=True
        Whether to commit the changes to the database.
    num_retries: int, default=3
        Number of times to retry the operation if there is a disconnection error.
    """

    for i in range(num_retries):
        try:
            with Session(engine) as session:
                # Add character into database
                for name, is_winner in zip((red, blue), (winner == 'red', winner == 'blue')):
                    update_character(session, name, is_winner)

                # Add match into database
                session.add(Match(red=red, blue=blue, winner=winner))

                # Add match metadata into database
                if pots is not None and (pots[0] != 0 and pots[1] != 0):
                    red_pot, blue_pot = pots
                    match_id = max(session.execute(select(Match.id)).scalars())
                    session.add(MatchMetadata(
                        match_id=match_id,
                        red_pot=red_pot,
                        blue_pot=blue_pot
                    ))

                if commit:
                    session.commit()

                logging.info(f"Added match successfully.")
                return  # No error, so return

        except OperationalError as e:
            if i == num_retries - 1:
                # Final retry, raise the exception
                raise e

            # Otherwise, retry after a short wait
            wait_time = 2 ** (i - 1)
            logging.warning(f"OperationalError: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


engine = sqlalchemy.create_engine(settings.PG_DSN, echo=False)
Base.metadata.create_all(engine)
