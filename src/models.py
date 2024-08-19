from .lib.model import MongoModel


class User(MongoModel):
    def __init__(
            self,
            user_id: str,
            platform: str,
            first_name: str,
            last_name: str = None,
            username: str = None,
            language: str = "en",
            is_active: bool = True,
            **kwargs
    ):
        super().__init__(user_id=user_id, platform=platform, first_name=first_name, last_name=last_name,
                         username=username, language=language, is_active=is_active, **kwargs)


class PriceRecord(MongoModel):
    def __init__(
            self,
            product_name: str,
            average_price: float,
            max_price: float,
            min_price: float,
            quantity: int,
            **kwargs
    ):
        super().__init__(product_name=product_name, average_price=average_price, max_price=max_price,
                         min_price=min_price, quantity=quantity, **kwargs)
