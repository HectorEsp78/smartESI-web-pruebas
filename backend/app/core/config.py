"""Application settings loaded from environment variables / ``.env``.

Electricity can read the real Home Assistant recorder when
``DATA_SOURCE=database``; with ``DATA_SOURCE=mock`` both tabs run without a
database. Lighting consumption always comes from the deterministic model, but
its occupancy can use the real counters when the recorder is available.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    # "mock"     -> synthetic data generated on the fly (no database needed).
    # "database" -> read from the real Home Assistant recorder DB (MariaDB).
    DATA_SOURCE: Literal["mock", "database"] = "database"

    # --- Home Assistant recorder connection ------------------------------------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "smartesi"
    DB_USER: str = "smartesi"
    DB_PASSWORD: str = "smartesi"
    DB_SSL: bool = True
    DB_SSL_CA: str = ""

    # --- Metric conversion factors ---------------------------------------------
    # Electricity price in euros per kWh and grid carbon intensity (kg CO2/kWh).
    ENERGY_PRICE_EUR_PER_KWH: float = 0.20
    CO2_KG_PER_KWH: float = 0.15
    # Plausibility cap for the hourly difference of the cumulative meter:
    # recorder imports / meter resets can add a single absurd jump to ``sum``.
    ENERGY_MAX_KWH_PER_HOUR: float = 150.0

    CORS_ALLOW_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"
    # Small in-memory cache for the expensive aggregated series.
    STATS_CACHE_TTL_SECONDS: int = 30
    # Timezone used for human-facing buckets (hours, days, months).
    TIMEZONE: str = "Europe/Madrid"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cors_allow_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.CORS_ALLOW_ORIGINS.split(",")
            if origin.strip()
        ]

        if self.is_production:
            if not origins:
                raise ValueError("CORS allowlist cannot be empty in production")
            if "*" in origins:
                raise ValueError("Wildcard CORS origin is forbidden in production")

        return origins


settings = Settings()
