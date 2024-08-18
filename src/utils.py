import aiohttp


class Helper:

    @staticmethod
    async def fetch_prices() -> list[dict] | None:
        """
        Fetches the latest product prices from the external API.

        Returns:
            list[dict] | None: A list of dictionaries containing product price information,
                or None if the request fails. Each dictionary represents a product with
                keys such as '_id', 'min', 'max', 'ort', and 'adet'.
        """
        async with aiohttp.ClientSession(read_timeout=3) as session:
            async with session.get("http://www.ktb.org.tr:9595/Home/GetGrnWebAnlikFiyat") as resp:
                product_list: list[dict] = await resp.json()
                return product_list

    @staticmethod
    def generate_price_list_text(product_list: list[dict]) -> str:
        """
        Generates a formatted text representation of the product price list.

        Args:
            product_list (list[dict]): A list of dictionaries containing product
                price information. Each dictionary should include keys such as
                '_id', 'min', 'max', 'ort', and 'adet'.

        Returns:
            str: A formatted string representing the price list, including minimum,
                maximum, and average prices, as well as the quantity for each product.
        """
        message = ""

        for product in product_list:
            name = product["urun"]
            min_price = round(product["min"], 3)
            max_price = round(product["max"], 3)
            mean_price = round(product["ort"], 3)
            quantity = product["adet"]
            emoji_pin = "\U0001F4CC"

            message += f"{emoji_pin}  <u><b>{name}</b></u>  {emoji_pin}\n"
            message += f"<b>En az:</b>   {min_price} TL\n"
            message += f"<b>En fazla:</b>   {max_price} TL\n"
            message += f"<b>Ortalama:</b>   {mean_price} TL\n"
            message += f"<b>Adet:</b>   {quantity} adet\n"
            message += "\n\n"

        return message
