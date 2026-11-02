from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Access the .env file using pydantic-settings"""

    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str
    database_drivername: str

    api_name: str
    api_version: str

    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_expiration_minute: int
    jwt_refresh_expiration_days: int

    #! MailJet Email Service Credentials
    mailjet_api_key: str
    mailjet_secret_key: str

    #! api request retry configurations
    max_retries: int
    base_delay: int
    max_delay: int

    model_config = SettingsConfigDict(env_file=".env")


config = Config()
