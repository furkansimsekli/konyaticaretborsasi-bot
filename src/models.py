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


class Product(MongoModel):
    def __init__(
            self,
            product_id: int,
            name: str,
            price: float,
            category: str,
            available: bool = True,
            **kwargs
    ):
        super().__init__(product_id=product_id, name=name, price=price, category=category, available=available,
                         **kwargs)
