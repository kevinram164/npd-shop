from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "noli-service"
    database_url: str = "sqlite:///./noli.db"
    cors_origins: str = "*"
    jwt_secret: str = "noli-dev-secret-change-me"
    jwt_expire_days: int = 7
    admin_email: str = "admin@noli.shop"
    admin_password: str = "admin123"
    bank_account_name: str = "CONG TY NOLI VIET NAM"
    bank_account_number: str = "0123456789"
    bank_name: str = "NPD Bank Demo"
    transfer_prefix: str = "NOLI"
    seed_on_startup: bool = True

    # Service discovery (compose / k8s DNS)
    auth_url: str = "http://127.0.0.1:8001"
    catalog_url: str = "http://127.0.0.1:8002"
    order_url: str = "http://127.0.0.1:8003"
    payment_url: str = "http://127.0.0.1:8004"

    kafka_bootstrap: str = ""
    kafka_orders_topic: str = "orders.events"
    kafka_payments_topic: str = "payments.events"
    kafka_security_protocol: str = ""
    kafka_sasl_mechanism: str = "SCRAM-SHA-512"
    kafka_username: str = "npd-shop"
    kafka_password: str = ""
    kafka_ssl_cafile: str = "/etc/kafka/certs/ca.crt"
    internal_token: str = "noli-internal-dev"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
