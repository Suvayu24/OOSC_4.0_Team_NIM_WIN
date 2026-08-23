from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "energy_resilience"
    gemini_api_key: str = ""

    # Risk-scoring calibration (see calibrate.py to tune these before changing them here)
    decay_lambda: float = 0.231   # ~3 day half-life: ln(2)/3
    logistic_k: float = 1.5
    logistic_r0: float = 2.0

    class Config:
        env_file = ".env"


settings = Settings()
