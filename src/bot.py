import datetime

import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, TypeHandler

from . import config, handler, task


def main() -> None:
    app: Application = Application.builder().token(config.TELEGRAM_API_TOKEN).build()

    app.add_handler(CommandHandler("start", handler.start), group=1)
    app.add_handler(CommandHandler("yardim", handler.help_), group=1)
    app.add_handler(CommandHandler("fiyatlar", handler.send_prices), group=1)
    app.add_handler(CommandHandler("son_7_gun", handler.last_7_days), group=1)
    app.add_handler(CommandHandler("son_15_gun", handler.last_15_days), group=1)
    app.add_handler(CommandHandler("son_30_gun", handler.last_30_days), group=1)
    app.add_handler(CommandHandler("bildirim_kapat", handler.disable_notifier), group=1)
    app.add_handler(CommandHandler("bildirim_ac", handler.enable_notifier), group=1)
    app.add_handler(CommandHandler("bagis", handler.donate), group=1)

    # In python-telegram-bot, handlers have something called group. It means that whenever there is
    # a new update from Telegram, this update runs through each of these groups. This update can be
    # handled by a handler from group 2, and it can be handled by another handler from group 7 at
    # the same time. Handling updates sounds like we have only one chance to do something at first,
    # but no. We can handle it however we like. Handlers are completely seperated and don't have any
    # relationship with Telegram. At least I had this misconception for a long time.
    #
    # So, I use grouping to switch context to another conversation, because otherwise updates stuck
    # inside the conversation. Alright then everything seems fine right? Nah...
    #
    # Conversation handling is a bit tricky, especially when it comes to nested conversations.
    # I want to have a really simple conversation flow with the users. It should be like following:
    # When the user starts a new conversation, let's call it conv_1, conversation should start
    # normally. Then, when she decides to start another conversation, let's say conv_2, it should
    # end the conv_1 and continue normally within the conv_2. There mustn't be a nested conversation!
    # Therefore, we need to kill the previous conversations. There isn't an obvious way to kill a
    # conversation unless you want to manually use _update_state() method. Here comes my tricky
    # solution. I put a MessageHandler into fallback that filters only commands. Fallback means if the
    # update can't be handled inside the states, it goes to fallbacks and see if it can find a proper
    # handler there. When user starts conv_2, she has to use a specific command let's say /start_conv_2.
    # conv_1_handler won't find a proper handler for /start_conv_2, so it will fall, then our tricky
    # MessageHandler will catch it. It will kill the current conversation. Then the update will travel
    # through other groups. This way we will have only one alive conversation. This tricky MessageHandler
    # is given below.
    conversation_switch_handler = MessageHandler(filters.COMMAND, handler.cancel)

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('admin_duyuru', handler.admin_announcement)],
        states={
            1: [MessageHandler(~filters.COMMAND, handler.admin_announcement_done)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, handler.conversation_timeout)]
        },
        fallbacks=[
            CommandHandler('bitti', handler.done),
            conversation_switch_handler
        ],
        allow_reentry=True,
        conversation_timeout=600
    ), group=2)

    app.add_error_handler(handler.err_handler)
    app.job_queue.run_repeating(callback=task.update_prices,
                                interval=config.PRICE_UPDATE_INTERVAL,
                                first=5)

    for i in range(len(config.PRICE_CHECK_HOURS)):
        hour, minute = config.PRICE_CHECK_HOURS[i], config.PRICE_CHECK_MINUTES[i]
        app.job_queue.run_daily(callback=task.check_and_notify_prices,
                                time=datetime.time(hour=hour, minute=minute, tzinfo=pytz.timezone("Europe/Istanbul")))

    if config.WEBHOOK_CONNECTED:
        app.run_webhook(listen=config.WEBHOOK_BIND,
                        port=int(config.PORT),
                        url_path=config.TELEGRAM_API_TOKEN,
                        webhook_url=config.WEBHOOK_URL)
    else:
        app.run_polling()
