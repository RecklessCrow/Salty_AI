from pydantic import FilePath, MongoDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Attributes
    ----------
    SALTYBET_USERNAME: str
        Username to your SaltyBet account.
    SALTYBET_PASSWORD: str
        Password to your SaltyBet account.
    """

    # Credentials
    SALTYBET_USERNAME: str
    SALTYBET_PASSWORD: str
    DB_DSN: MongoDsn

    # Files
    MODEL_PATH: FilePath
    FIREFOX_BIN: FilePath

    # How long to wait in while loops (seconds)
    WAIT_TIME: int = 5
    STATE_UPDATE_INTERVAL: int = 1


config = Settings()
