from pydantic import (
    BaseSettings,
    PostgresDsn,
    DirectoryPath,
    FilePath,
    validator,
)


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
    MODEL_DIR: FilePath
        Path to the onnx file to load.
    """

    # Credentials
    SALTYBET_USERNAME: str
    SALTYBET_PASSWORD: str
    PG_DSN: PostgresDsn = None  # Optional

    # Files
    MODEL_DIR: DirectoryPath = None
    # JSON_PATH: FilePath = None

    # How long to wait in while loops (seconds)
    WAIT_TIME: int = 5
    STATE_UPDATE_INTERVAL: int = 1

    @validator('MODEL_DIR')
    def model_validator(cls, v):
        # If we don't have a model, don't validate it
        if v is None:
            return None

        import onnx
        import os
        model = onnx.load(os.path.join(v, 'model.onnx'))
        onnx.checker.check_model(model)

        return str(v)


settings = Settings()
