from enum import Enum

import onnx
from pydantic import (
    BaseSettings,
    PostgresDsn,
    FilePath,
    validator
)


class States(Enum):
    START = 0
    BETS_OPEN = 1
    BETS_CLOSED = 2
    PAYOUT = 3


class Settings(BaseSettings):
    """
    Attributes
    ----------
    SALTYBET_USERNAME: str
        Username to your SaltyBet account.
    SALTYBET_PASSWORD: str
        Password to your SaltyBet account.
    PG_DSN: PostgresDsn
        Postgres Database.
    MODEL_PATH: FilePath
        Path to the onnx file to load.
    """

    # Saltybet Creds
    SALTYBET_USERNAME: str
    SALTYBET_PASSWORD: str

    # Database creds
    PG_DSN: PostgresDsn

    # Model
    MODEL_PATH: FilePath = None

    # Constants
    WAIT_TIME: int = 2
    LINE_SEPERATOR = "-" * 100

    @validator('MODEL_PATH')
    def model_validator(cls, v):
        """
        Validate the onnx development using ``onnx.checker.check_model``.

        Parameters
        ----------
        v : FilePath
            File path to the onnx development.

        Returns
        -------
        str
            File path to the onnx development.
        """
        if v is None:
            return None

        model = onnx.load(v)
        onnx.checker.check_model(model)

        return str(v)


settings = Settings()
