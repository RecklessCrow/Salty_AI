from pydantic import BaseSettings, PostgresDsn, FilePath, validator
import onnx


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
    MODEL_PATH: FilePath

    @validator('MODEL_PATH')
    def model_validator(cls, v):
        """
        Validate the onnx model using ``onnx.checker.check_model``.

        Parameters
        ----------
        v : FilePath
            File path to the onnx model.

        Returns
        -------
        str
            File path to the onnx model.
        """
        model = onnx.load(v)
        onnx.checker.check_model(model)

        return str(v)


settings = Settings()
