from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NOLI Shop"
    database_url: str = "sqlite:///./noli.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    bank_account_name: str = "CONG TY NOLI VIET NAM"
    bank_account_number: str = "0123456789"
    bank_name: str = "NPD Bank Demo"
    transfer_prefix: str = "NOLI"
    seed_on_startup: bool = True
    jwt_secret: str = "noli-dev-secret-change-me"
    jwt_expire_days: int = 7
    admin_email: str = "admin@noli.shop"
    admin_password: str = "admin123"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
