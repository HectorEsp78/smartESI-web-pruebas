"""Application settings loaded from environment variables / ``.env``.

The defaults are tuned for *local development* of the statistics prototype:
the app runs with synthetic data (``DATA_SOURCE=mock``) and does not need a
database. When you are ready to connect to the real Home Assistant recorder
database, set ``DATA_SOURCE=database`` and fill in the ``DB_*`` values.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # "mock"     -> synthetic data generated on the fly (no database needed).
    # "database" -> read from the real Home Assistant recorder DB (MariaDB).
    DATA_SOURCE: Literal["mock", "database"] = "mock"

    # --- Future database connection (only used when DATA_SOURCE=database) -------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "smartesi"
    DB_USER: str = "smartesi"
    DB_PASSWORD: str = "smartesi"
    DB_SSL: bool = True
    DB_SSL_CA: str = ""

    # --- Metric conversion factors used by the energy charts -------------------
    # Price of one kWh of electricity in euros and the grid carbon intensity
    # (kg CO2 per kWh). Gas has its own price and emission factor.
    ENERGY_PRICE_EUR_PER_KWH: float = 0.20
    CO2_KG_PER_KWH: float = 0.15
    GAS_PRICE_EUR_PER_KWH: float = 0.06
    GAS_CO2_KG_PER_KWH: float = 0.20
    # Outdoor temperature below which heating is considered necessary. Used to
    # compute heating degree-days (base 18 °C by default).
    HEATING_BASE_TEMPERATURE_C: float = 18.0

    CORS_ALLOW_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"
    # Small in-memory cache for the (expensive) aggregated series.
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
