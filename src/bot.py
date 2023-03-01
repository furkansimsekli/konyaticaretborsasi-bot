import datetime
import html
import json
import logging
import traceback

import aiohttp
import pytz
import telegram.constants
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import TELEGRAM_API_KEY, DB_STRING, WEBHOOK_CONNECTED, WEBHOOK_URL, PORT, LOGGER_CHAT_ID, ADMIN_ID, \
    PRICE_CHECK_HOURS, PRICE_CHECK_MINUTES
from .mongo import UserDatabase

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger()

# Database
USER_DB = UserDatabase(DB_STRING)


# Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await USER_DB.find(user_id)

    if not user:
        await USER_DB.new_user(user_id, update.effective_user.first_name, update.effective_user.last_name)

    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="Hoşgeldin! Konya Ticaret Borsasından anlık fiyatları öğrenmek için doğru "
                                        "yerdesin. /fiyatlar komutu ile fiyatları öğrenebilirsin. Ayrıca ben sana "
                                        "otomatik olarak belirli saatlerde bildirim göndereceğim!\n\n"
                                        "Eğer bu bildirimleri almak istemiyorsan /bildirim_kapat komutunu "
                                        "kullanabilirsin!")


async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="/fiyatlar - Anlık fiyat tablosu\n"
                                        "/bildirim_kapat - Otomatik bildirimleri kapat\n"
                                        "/bildirim_ac - Otomatik bildirimleri aç\n"
                                        "/bagis - Geliştiriciye bağış yap")


async def send_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = create_formatted_text(await get_prices())
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=message,
                                   parse_mode=telegram.constants.ParseMode.HTML)


async def disable_notifier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await USER_DB.find(user_id)

    if not user["dnd"]:
        await USER_DB.toggle_notify_status(user_id)
        await context.bot.send_message(chat_id=user_id,
                                       text="Bundan sonra otomatik fiyat bildirimi göndermeyeceğim. Tekrardan açmak "
                                            "için /bildirim_ac komutunu kullan!")
    else:
        await context.bot.send_message(chat_id=user_id,
                                       text="Sana zaten otomatik bir şekilde fiyat tablosunu göndermiyorum. Açmak "
                                            "istiyorsan /bildirim_ac komutunu kullanabilirsin.")


async def enable_notifier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await USER_DB.find(user_id)

    if user["dnd"]:
        await USER_DB.toggle_notify_status(user_id)
        await context.bot.send_message(chat_id=user_id,
                                       text="Tamamdır, seni de abone listesine ekledim! Bundan sonra günlük mesaj "
                                            "göndereceğim fiyatlar hakkında!")
    else:
        await context.bot.send_message(chat_id=user_id,
                                       text="Sana zaten günlük fiyat tablosunu gönderiyorum. Kapatmak istiyorsan "
                                            "/bildirim_kapat komutunu kullanabilirsin.")


async def admin_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await context.bot.send_message(chat_id=user_id,
                                       text="Bu komutu kullanmak için yetkin yok!")
        return

    # Message: /<command> <message> --- ignore "/<command>" text, accept only <message> part.
    admin_message = ' '.join(update.message.text.split()[1:])
    user_list = await USER_DB.find_all()

    for target in user_list:
        try:
            await context.bot.send_message(chat_id=target,
                                           text=admin_message,
                                           parse_mode=telegram.constants.ParseMode.HTML)
            logger.info(f"Message has been sent to {target}")
        except telegram.error.Forbidden:
            logger.info(f"FORBIDDEN: Message couldn't be delivered to {target}")


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "@konyaticaretborsasi_bot deneyiminden memnunsan geliştiriciye atıştırmalık bir şey alabilirsin!\n\n" \
              "<b>₺:</b> <code>TR76 0011 1000 0000 0109 8128 40</code>\n" \
              "<b>$:</b> <code>TR36 0011 1000 0000 0113 1638 43</code>\n" \
              "<b>€:</b> <code>TR68 0011 1000 0000 0113 1638 49</code>\n\n" \
              "Enpara: <code>Furkan Şimşekli</code>"

    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=message,
                                   parse_mode=telegram.constants.ParseMode.HTML)


# Task
async def check_prices(context: ContextTypes.DEFAULT_TYPE) -> None:
    message = create_formatted_text(await get_prices())
    user_list = await USER_DB.find_all(dnd=False)

    for target in user_list:
        try:
            await context.bot.send_message(chat_id=target, text=message, parse_mode=telegram.constants.ParseMode.HTML)
            logger.info(f"Message has been sent to {target}")
        except telegram.error.Forbidden:
            logger.info(f"FORBIDDEN: Message couldn't be delivered to {target}")
        except telegram.error.BadRequest:
            logger.info(f"FORBIDDEN: Message couldn't be delivered to {target}")
            continue


# Error Handler
async def err_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Below code belongs to python-telegram-bot examples.
    Url: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/errorhandlerbot.py
    """

    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    await context.bot.send_message(chat_id=LOGGER_CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.HTML)


# Utils
async def get_prices() -> list[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://www.ktb.org.tr:9595/Home/GetGrnWebAnlikFiyat") as resp:
            product_list: list[dict] = await resp.json()
            for product in product_list:
                product['_id'] = product.pop('urun')
            return product_list


def create_formatted_text(product_list: list[dict]) -> str:
    message = ""

    for product in product_list:
        name = product["_id"]
        min_price = round(product["min"], 3)
        max_price = round(product["max"], 3)
        mean_price = round(product["ort"], 3)
        quantity = product["adet"]

        message += f"\U0001F4CC  <u><b>{name}</b></u>  \U0001F4CC\n"
        message += f"<b>En az:</b>   {min_price} TL\n"
        message += f"<b>En fazla:</b>   {max_price} TL\n"
        message += f"<b>Ortalama:</b>   {mean_price} TL\n"
        message += f"<b>Adet:</b>   {quantity} adet\n"
        message += "\n\n"
    return message


def main() -> None:
    app: Application = Application.builder().token(TELEGRAM_API_KEY).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('yardim', help_))
    app.add_handler(CommandHandler("fiyatlar", send_prices))
    app.add_handler(CommandHandler("bildirim_kapat", disable_notifier))
    app.add_handler(CommandHandler("bildirim_ac", enable_notifier))
    app.add_handler(CommandHandler("admin_duyuru", admin_announcement))
    app.add_handler(CommandHandler("bagis", donate))
    app.add_error_handler(err_handler)

    tz = pytz.timezone("Europe/Istanbul")

    for i in range(len(PRICE_CHECK_HOURS)):
        hour, minute = PRICE_CHECK_HOURS[i], PRICE_CHECK_MINUTES[i]
        app.job_queue.run_daily(check_prices, time=datetime.time(hour=hour, minute=minute, tzinfo=tz))

    if WEBHOOK_CONNECTED:
        app.run_webhook(listen="0.0.0.0",
                        port=int(PORT),
                        url_path=TELEGRAM_API_KEY,
                        webhook_url=WEBHOOK_URL)
    else:
        app.run_polling()
