from datetime import datetime
from io import BytesIO

import aiohttp
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class Helper:

    @staticmethod
    async def fetch_prices() -> dict | None:
        """
        Fetches the latest product prices from the external API.

        Returns:
            dict | None: A dictionary containing product information by product groups,
                or None if the request fails.
        """
        today_date = datetime.today().strftime('%Y-%m-%d')
        groups = dict()

        async with aiohttp.ClientSession(read_timeout=3) as session:
            async with session.get(f"https://www.ktb.org.tr/api/v1/Alpha.WebPanel/OnlineKullaniciBulten/GetAnlikBulten/{today_date}", ssl=False) as resp:
                product_list: list[dict] = await resp.json()

                for product in product_list:
                    product_name = product["UrunGrubu"]
                    product_quantity = product["TopMiktar"]
                    product_max_price = float(product["MaxFiyat"].replace(',', '.'))
                    product_min_price = float(product["MinFiyat"].replace(',', '.'))
                    product_avg_price = float(product["AvgFiyat"].replace(',', '.'))

                    group_name = product["GrupAdi"]
                    group_max_price = product["GrupMaxFiyat"] / 10**4
                    group_min_price = product["GrupMinFiyat"] / 10**4
                    group_avg_price = product["GrupOrtFiyat"] / 10**4

                    if group_name not in groups:
                        groups[group_name] = {
                            "products": [],
                            "group_max_price": group_max_price,
                            "group_min_price": group_min_price,
                            "group_avg_price": group_avg_price,
                            "group_quantity": 0
                        }

                    groups[group_name]["products"].append({
                        "name": product_name,
                        "quantity": product_quantity,
                        "max_price": product_max_price,
                        "min_price": product_min_price,
                        "avg_price": product_avg_price
                    })
                    groups[group_name]["group_quantity"] += product_quantity

                return groups

    @staticmethod
    def generate_price_list_text(groups: dict) -> str:
        """
        Generates a formatted text representation of the product price list.

        Args:
            groups (dict): A dictionary containing product information by product groups.

        Returns:
            str: A formatted string representing the price list, including minimum,
                maximum, and average prices, as well as the quantity for each product.
        """
        message = ""

        for name, group in groups.items():
            min_price = f"{group["group_min_price"]:.2f}".replace(".", ",")
            max_price = f"{group["group_max_price"]:.2f}".replace(".", ",")
            avg_price = f"{group["group_avg_price"]:.2f}".replace(".", ",")
            quantity = f"{group["group_quantity"]:,}".replace(",", ".")
            emoji_pin = "\U0001F4CC"

            message += f"{emoji_pin}  <u><b>{name}</b></u>  {emoji_pin}\n"
            message += f"<b>En az:</b>   {min_price} TL\n"
            message += f"<b>En fazla:</b>   {max_price} TL\n"
            message += f"<b>Ortalama:</b>   {avg_price} TL\n"
            message += f"<b>Miktar:</b>   {quantity} KG\n"
            message += "\n\n"

        return message

    @staticmethod
    def generate_price_graph(data: list, days) -> BytesIO:
        product_data = {}

        for item in data:
            if item.product_name not in product_data:
                product_data[item.product_name] = {"dates": [], "prices": []}

            product_data[item.product_name]["dates"].append(item.created_at.date())
            product_data[item.product_name]["prices"].append(item.average_price)

        plt.figure(figsize=(12, 8))

        # Generate a different color for each product
        colors = plt.get_cmap("tab20").colors
        legend_lines = []

        for idx, (product_name, values) in enumerate(product_data.items()):
            plt.plot(values["dates"],
                     values["prices"],
                     marker="o",
                     linestyle="-",
                     color=colors[idx % len(colors)],
                     label=product_name)
            legend_lines.append(Line2D([0], [0], color=colors[idx % len(colors)], lw=2, label=product_name))

        plt.title(f"Konya Ticaret Borsası Son {days} Günün Fiyat Grafiği")
        plt.ylabel("Ortalama Fiyat (TL)")

        # Format x-axis dates automatically
        ax = plt.gca()
        if days <= 7:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        elif days <= 30:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))

        plt.legend(handles=legend_lines, loc='upper left', bbox_to_anchor=(1, 1), frameon=False)
        plt.grid(True)

        buf = BytesIO()
        plt.savefig(buf, format="PNG", bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
