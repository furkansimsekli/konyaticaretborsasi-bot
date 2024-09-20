import asyncio
from datetime import datetime

import telegram
from telegram.ext import ContextTypes

from . import config
from .app import PriceRecord, User, logger
from .utils import Helper


async def check_and_notify_prices(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        prices = await Helper.fetch_prices()
    except asyncio.exceptions.TimeoutError:
        logger.error("Can't access to market servers at the moment.")
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text="Borsa sunucularına ulaşılamıyor.")
        return

    if not prices:
        logger.warn("There isn't any price information at the market.")
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text="Şu anda fiyat bilgisi bulunmamaktadır.")
        return

    user_list = await User.find_all({"dnd": False, "platform": "Telegram"})
    inactive_user_ids = []
    message = Helper.generate_price_list_text(prices)

    for target_user in user_list:
        try:
            await context.bot.send_message(chat_id=target_user.user_id,
                                           text=message,
                                           parse_mode=telegram.constants.ParseMode.HTML)
            logger.info(f"Message has been sent to {target_user.user_id}")
        except (telegram.error.Forbidden, telegram.error.BadRequest):
            logger.info(f"Message couldn't be delivered to {target_user.user_id}")
            inactive_user_ids.append(target_user.user_id)
            continue

    if inactive_user_ids:
        await User.update_many(query={"user_id": {"$in": inactive_user_ids}},
                               update_data={"is_active": False})


async def update_prices(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        records = await Helper.fetch_prices()
    except asyncio.exceptions.TimeoutError:
        logger.error("Can't access the market servers at the moment.")
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text="Borsa sunucularına ulaşılamıyor.")
        return

    if not records:
        logger.warn("There isn't any price information at the market.")
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text="Şu anda fiyat bilgisi bulunmamaktadır.")
        return

    product_names = [record["urun"] for record in records]
    today = datetime.now().date()
    existing_records = await PriceRecord.find_all({
        "product_name": {"$in": product_names},
        "created_at": {"$gte": today}
    })
    object_ids_to_delete = [record._id for record in existing_records]
    price_records_to_save = []

    for record in records:
        product = PriceRecord(product_name=record["urun"],
                              average_price=record["ort"],
                              max_price=record["max"],
                              min_price=record["min"],
                              quantity=record["adet"])
        price_records_to_save.append(product)

    await PriceRecord.insert_many(price_records_to_save)
    logger.info("New market data has been inserted into the database.")

    if object_ids_to_delete:
        await PriceRecord.delete_many({"_id": {"$in": object_ids_to_delete}})
        logger.info("Old price records have been deleted from the database.")
