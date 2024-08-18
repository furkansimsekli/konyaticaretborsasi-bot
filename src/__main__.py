from . import bot
from . import config


def validate():
    if not config.TELEGRAM_API_TOKEN:
        print("ERROR: Please configure TELEGRAM API TOKEN")
        exit(-1)

    if not config.MONGODB_URI:
        print("ERROR: Please configure MONGODB_URI")
        exit(-1)

    if not config.DATABASE_NAME:
        print("ERROR: Please configure DATABASE_NAME")
        exit(-1)

    if not config.ADMIN_CHAT_ID:
        print("WARNING: You didn't configure an ADMIN_CHAT_ID, so you won't be able to use admin commands!")

    if not config.LOGGER_CHAT_ID:
        print("ERROR: Please configure LOGGER_CHAT_ID")
        exit(-1)

    if not config.PRICE_CHECK_HOURS:
        print("WARNING: You didn't configure PRICE_CHECK_HOURS, there won't be scheduled jobs to notify users!")

    if not config.PRICE_CHECK_MINUTES:
        print("WARNING: You didn't configure PRICE_CHECK_MINUTES, there won't be scheduled jobs to notify users!")

    elif len(config.PRICE_CHECK_HOURS) != len(config.PRICE_CHECK_MINUTES):
        print("ERROR: Please make sure time configurations are correct. Hours and minutes list must be same size!")
        exit(-1)

    if config.WEBHOOK_CONNECTED:
        if not config.WEBHOOK_URL or config.WEBHOOK_URL == f"/{config.TELEGRAM_API_TOKEN}":
            print("ERROR: Please make sure you configured a WEBHOOK_URL if you are using webhook rather than polling!")
            exit(-1)

        if not config.PORT:
            print("ERROR: Please configure PORT")
            exit(-1)

        if not config.WEBHOOK_BIND:
            print("ERROR: Please configure WEBHOOK_BIND")
            exit(-1)


if __name__ == "__main__":
    validate()
    bot.main()
