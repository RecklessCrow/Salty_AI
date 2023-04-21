from pydantic import (
    BaseSettings,
    FilePath,
)


class WebSettings(BaseSettings):
    JSON_PATH: FilePath


settings = WebSettings()
