import datetime

import pytz
from telegram.ext import Application, CommandHandler

from . import config, handler, task


def main() -> None:
    app: Application = Application.builder().token(config.TELEGRAM_API_KEY).build()

    app.add_handler(CommandHandler('start', handler.start))
    app.add_handler(CommandHandler('yardim', handler.help_))
    app.add_handler(CommandHandler("fiyatlar", handler.send_prices))
    app.add_handler(CommandHandler("bildirim_kapat", handler.disable_notifier))
    app.add_handler(CommandHandler("bildirim_ac", handler.enable_notifier))
    app.add_handler(CommandHandler("admin_duyuru", handler.admin_announcement))
    app.add_handler(CommandHandler("bagis", handler.donate))
    app.add_error_handler(handler.err_handler)

    tz = pytz.timezone("Europe/Istanbul")

    for i in range(len(config.PRICE_CHECK_HOURS)):
        hour, minute = config.PRICE_CHECK_HOURS[i], config.PRICE_CHECK_MINUTES[i]
        app.job_queue.run_daily(task.check_and_notify_prices, time=datetime.time(hour=hour, minute=minute, tzinfo=tz))

    if config.WEBHOOK_CONNECTED:
        app.run_webhook(listen="0.0.0.0",
                        port=int(config.PORT),
                        url_path=config.TELEGRAM_API_KEY,
                        webhook_url=config.WEBHOOK_URL)
    else:
        app.run_polling()
