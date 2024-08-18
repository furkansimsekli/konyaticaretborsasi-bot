import os

import toml

config_path = os.environ.get("CONFIG_PATH")

if config_path is None:
    raise ValueError("CONFIG_PATH environment variable is not set")

config = toml.load(config_path)

TELEGRAM_API_TOKEN: str = config.get("TELEGRAM_API_TOKEN")
MONGODB_URI: str = config.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME: str = config.get("DATABASE_NAME", "ktb-db-test")

# Chat ID Constants
ADMIN_CHAT_ID: int = config.get("ADMIN_CHAT_ID")
LOGGER_CHAT_ID: int = config.get("LOGGER_CHAT_ID")

# Time Configurations for the Price Checking Task
PRICE_CHECK_HOURS: list[int] = config.get("PRICE_CHECK_HOURS", [10, 15])
PRICE_CHECK_MINUTES: list[int] = config.get("PRICE_CHECK_MINUTES", [0, 0])

# Polling or Webhook?
WEBHOOK_CONNECTED: bool = config.get("WEBHOOK_CONNECTED", False)
PORT: int = config.get("PORT", 9999)
WEBHOOK_URL: str = config.get("WEBHOOK_URL", "") + "/" + TELEGRAM_API_TOKEN
WEBHOOK_BIND: str = config.get("WEBHOOK_BIND", "0.0.0.0")
