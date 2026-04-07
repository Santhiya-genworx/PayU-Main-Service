"""Module: settings.py"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the PayU Main Service API. This class defines all the necessary configuration parameters required for the application to function properly, including database connection details, JWT token settings, service URLs, and CORS origins. The settings are loaded from environment variables or a .env file, allowing for easy configuration management across different environments (development, staging, production). Each field in the class corresponds to a specific configuration parameter, and the class is designed to be easily extendable for future configuration needs. The model_config attribute specifies that the settings should be loaded from a .env file, making it convenient to manage sensitive information and environment-specific configurations without hardcoding them into the application."""

    db_user: str
    db_name: str
    db_host: str
    db_password: str
    db_port: int
    db_url: str

    access_secret_key: str
    access_token_expire_minutes: int
    refresh_secret_key: str
    refresh_token_expire_days: int
    algorithm: str

    auth_service_url: str
    process_service_url: str

    origins: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
