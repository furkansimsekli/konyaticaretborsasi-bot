# Telegram Bot Token
TELEGRAM_API_KEY: str = ''

# MongoDB Connection String
DB_STRING: str = ''

# Admin Chat ID
ADMIN_ID: int = 0

# Logger Chat ID
LOGGER_CHAT_ID: int = 0

# Time Configurations for the Price Checking Task
PRICE_CHECK_HOURS: list[int] = []
PRICE_CHECK_MINUTES: list[int] = []

# Polling or Webhook?
WEBHOOK_CONNECTED: bool = False
PORT: str = ''
WEBHOOK_URL: str = '' + TELEGRAM_API_KEY
