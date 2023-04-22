import sqlalchemy
from sqlalchemy import ForeignKey, select, Identity
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, Session

from app.utils.settings import settings


class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(Identity())
    name: Mapped[str] = mapped_column(primary_key=True)
    num_wins: Mapped[int] = mapped_column(nullable=False)
    num_matches: Mapped[int] = mapped_column(nullable=False)


class Match(Base):
    """

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

    """
    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    bet_on: Mapped[str] = mapped_column(nullable=False)
    amount_bet: Mapped[float] = mapped_column(nullable=False)
    payout: Mapped[int] = mapped_column(nullable=False)


def add_match(red, blue, winner, pots=None, commit=True):
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
    """

    with Session(engine) as session:
        # Add character into database
        for name, is_winner in zip((red, blue), (winner == 'red', winner == 'blue')):
            stmt = select(Character).where(Character.name == name)
            result = session.execute(stmt).first()

            if result is None:
                # Character does not exist in database, so add it
                session.add(Character(name=name, num_wins=int(is_winner), num_matches=1))
            else:
                # Character exists in database, so update it
                character = result[0]
                character.num_wins += int(is_winner)
                character.num_matches += 1

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


engine = sqlalchemy.create_engine(settings.PG_DSN, echo=False)
Base.metadata.create_all(engine)
