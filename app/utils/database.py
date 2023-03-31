import os

import sqlalchemy
from sqlalchemy import ForeignKey, select, Identity
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, Session

from app.utils.settings import settings

engine = sqlalchemy.create_engine(settings.PG_DSN, echo=False)


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


def add_match(match_info: tuple, session: Session, match_metadata=None, model_metadata=None, commit=True):
    """

    Parameters
    ----------
    match_info
    session
    match_metadata
    model_metadata
    commit

    Returns
    -------

    """
    red, blue, winner = match_info

    # Add character into database
    for name, is_winner in zip((red, blue), (winner == 'red', winner == 'blue')):
        stmt = select(Character).where(Character.name == name)
        obj = session.scalars(stmt).one_or_none()

        if obj is None:
            session.add(Character(name=name, num_wins=0, num_matches=0))
            session.commit()
            obj = session.scalars(stmt).one()

        obj.num_matches += 1
        obj.num_wins += 1 if is_winner else 0

    # Add match to database
    session.add(Match(
        red=red,
        blue=blue,
        winner=winner
    ))
    match_id = max(session.scalars(select(Match.id)))

    if match_metadata is not None:
        red_pot, blue_pot = match_metadata
        session.add(MatchMetadata(
            match_id=match_id,
            red_pot=red_pot,
            blue_pot=blue_pot
        ))

    if model_metadata is not None:
        model_name, confidence, bet_on, amount_bet, payout = model_metadata
        session.add(ModelMetadata(
            match_id=match_id,
            model_id=model_name,
            confidence=confidence,
            bet_on=bet_on,
            amount_bet=amount_bet,
            payout=payout
        ))

    if commit:
        session.commit()


def get_idxs(red_name: str, blue_name: str, session: Session):
    red = session.scalar(select(Character.id).where(Character.name == red_name))
    blue = session.scalar(select(Character.id).where(Character.name == blue_name))
    return red, blue


Base.metadata.create_all(engine)
