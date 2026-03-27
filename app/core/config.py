import os
from dataclasses import dataclass, field



def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    app_title: str = os.getenv("APP_TITLE", "父亲财务监管系统")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://4Azm2c71xKGJzVb.root:G8Ch4jZmQgOGeLKA@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/finance_manager?ssl_verify_cert=true&ssl_verify_identity=true",
    )
    timezone: str = os.getenv("APP_TIMEZONE", "Asia/Shanghai")
    default_page_limit: int = int(os.getenv("DEFAULT_PAGE_LIMIT", "100"))
    cors_allow_origins: tuple[str, ...] = field(
        default_factory=lambda: _split_csv(os.getenv("CORS_ALLOW_ORIGINS", "*"))
    )
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    cors_allow_methods: tuple[str, ...] = field(
        default_factory=lambda: _split_csv(os.getenv("CORS_ALLOW_METHODS", "*"))
    )
    cors_allow_headers: tuple[str, ...] = field(
        default_factory=lambda: _split_csv(os.getenv("CORS_ALLOW_HEADERS", "*"))
    )


settings = Settings()
