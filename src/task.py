import asyncio
from datetime import datetime, timedelta

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
        groups = await Helper.fetch_prices()
    except asyncio.exceptions.TimeoutError:
        logger.error("Can't access the market servers at the moment.")
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text="Borsa sunucularına ulaşılamıyor.")
        return

    if not groups:
        logger.warn("There isn't any price information at the market.")
        await context.bot.send_message(chat_id=config.LOGGER_CHAT_ID,
                                       text="Şu anda fiyat bilgisi bulunmamaktadır.")
        return

    group_names = list(groups.keys())
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    existing_records = await PriceRecord.find_all({
        "product_name": {"$in": group_names},
        "created_at": {"$gte": today_start, "$lt": today_end}
    })
    object_ids_to_delete = [record._id for record in existing_records]
    price_records_to_save = []

    for name, group in groups.items():
        product = PriceRecord(product_name=name,
                              average_price=group["group_avg_price"],
                              max_price=group["group_max_price"],
                              min_price=group["group_min_price"],
                              quantity=group["group_quantity"])
        price_records_to_save.append(product)

    await PriceRecord.insert_many(price_records_to_save)
    logger.info("New market data has been inserted into the database.")

    if object_ids_to_delete:
        await PriceRecord.delete_many({"_id": {"$in": object_ids_to_delete}})
        logger.info("Old price records have been deleted from the database.")
