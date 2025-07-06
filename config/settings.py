from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql://liquidity_user:your_secure_password@localhost:5432/liquidity_db"
    )
    redis_url: str = "redis://localhost:6379/0"

    # Solana
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    solana_wss_url: str = "wss://api.mainnet-beta.solana.com"
    solana_commitment: str = "confirmed"

    # APIs
    dexscreener_base_url: str = "https://api.dexscreener.com/latest"
    jupiter_base_url: str = "https://quote-api.jup.ag/v6"

    # Monitoring & Alerts (Optional)
    sentry_dsn: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # ML & Training
    mlflow_tracking_uri: str = "http://localhost:5000"
    model_retrain_interval: int = 3600  # seconds

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    debug: bool = False

    # Security
    secret_key: str = "your_super_secret_key_here"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        # Allow extra fields for future expansion
        extra = "ignore"


settings = Settings()
