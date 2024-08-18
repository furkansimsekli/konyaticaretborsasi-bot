import sys

import toml

config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.toml'
config = toml.load(config_path)

# Telegram Bot Token
TELEGRAM_API_KEY: str = config['TELEGRAM_API_KEY']

# MongoDB Connection String
DB_STRING: str = config['DB_STRING']
DB_NAME: str = config['DB_NAME']

# Admin Chat ID
ADMIN_ID: int = config['ADMIN_ID']

# Logger Chat ID
LOGGER_CHAT_ID: int = config['LOGGER_CHAT_ID']

# Time Configurations for the Price Checking Task
PRICE_CHECK_HOURS: list[int] = config['PRICE_CHECK_HOURS']
PRICE_CHECK_MINUTES: list[int] = config['PRICE_CHECK_MINUTES']

# Polling or Webhook?
WEBHOOK_CONNECTED: bool = config['WEBHOOK_CONNECTED']
PORT: str = config['PORT']
WEBHOOK_URL: str = config['WEBHOOK_URL']
