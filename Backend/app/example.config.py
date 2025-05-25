
from pydantic_settings import BaseSettings, SettingsConfigDict

# List of devices for initialization
DEVICES = [
    {"id": 1, "name": "Washing Machine 1", "type": "washer", "hourly_cost": 1.20},
    {"id": 2, "name": "Washing Machine 2", "type": "washer", "hourly_cost": 1.20},
    {"id": 3, "name": "Washing Machine 3", "type": "washer", "hourly_cost": 1.20},
    {"id": 4, "name": "Dryer 1", "type": "dryer", "hourly_cost": 1.50},
    {"id": 5, "name": "Dryer 2", "type": "dryer", "hourly_cost": 1.50},
]

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Waschplan API"
    API_VERSION: str = "1.0.0"
    
    # Database settings
    DATABASE_URL: str = "mysql+aiomysql://admin:password@localhost:3306/waschplan"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]  # Allow all origins
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

# Create settings instance
settings = Settings()
