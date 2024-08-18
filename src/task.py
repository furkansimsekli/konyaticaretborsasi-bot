import asyncio

import telegram
from telegram.ext import ContextTypes

from . import config
from .app import User, logger
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
