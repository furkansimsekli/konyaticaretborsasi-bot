import asyncio
import html
import json
import traceback

import telegram
from telegram import Update
from telegram.ext import ContextTypes

from . import config
from .app import PriceRecord, User, logger
from .utils import Helper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    user = await User.find_one({"user_id": str(telegram_user.id), "platform": "Telegram"})

    if not user:
        new_user = User(user_id=str(telegram_user.id),
                        platform="Telegram",
                        first_name=telegram_user.first_name,
                        last_name=telegram_user.last_name,
                        username=telegram_user.username,
                        language=telegram_user.language_code,
                        dnd=False)
        await new_user.save()

    await context.bot.send_message(chat_id=str(telegram_user.id),
                                   text="Hoş geldin! Konya Ticaret Borsasından anlık fiyatları öğrenmek için doğru "
                                        "yerdesin. /fiyatlar komutu ile fiyatları öğrenebilirsin.\n\n"
                                        "Daha fazla komut için /yardim 'a göz unutma!")


async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="/fiyatlar - Anlık fiyat tablosu\n"
                                        "/son_7_gun - Son 7 güne ait ortalama fiyat grafiği\n"
                                        "/son_15_gun - Son 15 güne ait ortalama fiyat grafiği\n"
                                        "/son_30_gun - Son 30 güne ait ortalama fiyat grafiği\n"
                                        "/bildirim_kapat - Otomatik bildirimleri kapat\n"
                                        "/bildirim_ac - Otomatik bildirimleri aç\n"
                                        "/bagis - Geliştiriciye bağış yap")


async def send_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        prices = await Helper.fetch_prices()
    except asyncio.exceptions.TimeoutError:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Bizden kaynaklı olmayan sebeplerden ötürü borsa sunucularına "
                                            "ulaşılamıyor, lütfen daha sonra tekrar deneyin.")
        return

    if not prices:
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Şu anda fiyat bilgisi bulunmamaktadır.")
        return

    message = Helper.generate_price_list_text(prices)
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=message,
                                   parse_mode=telegram.constants.ParseMode.HTML)


async def send_price_graph(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "max_date": {"$max": "$created_at"}
            }
        },
        {
            "$sort": {"max_date": -1}
        },
        {
            "$limit": days
        }
    ]

    unique_dates = await PriceRecord.aggregate(pipeline)

    if not unique_dates:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{days} günlük veri mevcut değil!")
        return

    unique_dates = [day["_id"] for day in unique_dates]
    price_data = await PriceRecord.find_all(
        query={"$expr": {"$in": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, unique_dates]}}
    )

    if not price_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{days} günlük veri mevcut değil!")
        return

    graph_image = Helper.generate_price_graph(price_data, days)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=graph_image)


async def last_7_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_price_graph(update, context, days=7)


async def last_15_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_price_graph(update, context, days=15)


async def last_30_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_price_graph(update, context, days=30)


async def disable_notifier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    user = await User.find_one({"user_id": str(telegram_user.id), "platform": "Telegram"})

    if not user.dnd:
        user.dnd = True
        await user.save()
        await context.bot.send_message(chat_id=telegram_user.id,
                                       text="Bundan sonra otomatik fiyat bildirimi göndermeyeceğim. Tekrardan açmak "
                                            "için /bildirim_ac komutunu kullan!")
    else:
        await context.bot.send_message(chat_id=telegram_user.id,
                                       text="Sana zaten otomatik bir şekilde fiyat tablosunu göndermiyorum. Açmak "
                                            "istiyorsan /bildirim_ac komutunu kullanabilirsin.")


async def enable_notifier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    user = await User.find_one({"user_id": str(telegram_user.id), "platform": "Telegram"})

    if user.dnd:
        user.dnd = False
        await user.save()
        await context.bot.send_message(chat_id=telegram_user.id,
                                       text="Tamamdır, seni de abone listesine ekledim! Bundan sonra günlük mesaj "
                                            "göndereceğim fiyatlar hakkında!")
    else:
        await context.bot.send_message(chat_id=telegram_user.id,
                                       text="Sana zaten günlük fiyat tablosunu gönderiyorum. Kapatmak istiyorsan "
                                            "/bildirim_kapat komutunu kullanabilirsin.")


async def admin_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user

    if telegram_user.id != config.ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=telegram_user.id,
                                       text="Bu komutu kullanmak için yetkin yok!")
        return

    # Message: /<command> <message> --- ignore "/<command>" text, accept only <message> part.
    admin_message = " ".join(update.message.text.split()[1:])
    user_list = await User.find_all({"platform": "Telegram"})
    inactive_user_ids = []

    for target_user in user_list:
        try:
            await context.bot.send_message(chat_id=target_user.user_id,
                                           text=admin_message,
                                           parse_mode=telegram.constants.ParseMode.HTML)
            logger.info(f"Message has been sent to {target_user.user_id}")
        except (telegram.error.Forbidden, telegram.error.BadRequest):
            logger.info(f"Message couldn't be delivered to {target_user.user_id}")
            inactive_user_ids.append(target_user.user_id)
            continue

    if inactive_user_ids:
        await User.update_many(query={"user_id": {"$in": inactive_user_ids}},
                               update_data={"is_active": False})


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("@konyaticaretborsasi_bot deneyiminden memnunsan geliştiriciye atıştırmalık bir şey alabilirsin!\n\n"
               "<b>₺:</b> <code>TR84 0011 1000 0000 0109 3410 82</code>\n"
               "<b>$:</b> <code>TR36 0011 1000 0000 0113 1638 43</code>\n"
               "<b>€:</b> <code>TR68 0011 1000 0000 0113 1638 49</code>\n\n"
               "Enpara: <code>Furkan Şimşekli</code>")

    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=message,
                                   parse_mode=telegram.constants.ParseMode.HTML)


async def err_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log the error and send a telegram message to notify the developer.

    Below code belongs to python-telegram-bot examples, furkansimsekli "fixed" the 4096 character limit.
    Url: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/errorhandlerbot.py
    """

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    traceback_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    traceback_string = "".join(traceback_list)
    traceback_message = f"{html.escape(traceback_string)}"

    # Build the message with some markup and additional information about what happened.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    ctx_msg = (f"An exception was raised while handling an update\n"
               f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
               f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
               f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n")
    await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                   text=ctx_msg,
                                   parse_mode=telegram.constants.ParseMode.HTML)

    if len(traceback_message) > 4096:
        tb_msg_list = traceback_message.split("The above exception was the direct cause of the following exception:")

        for traceback_message in tb_msg_list:
            if len(traceback_message) > 4096:
                await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                               text=f"Traceback is too long!",
                                               parse_mode=telegram.constants.ParseMode.HTML)
            else:
                await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                               text=f"<pre>{traceback_message}</pre>",
                                               parse_mode=telegram.constants.ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text=f"<pre>{traceback_message}</pre>",
                                       parse_mode=telegram.constants.ParseMode.HTML)
