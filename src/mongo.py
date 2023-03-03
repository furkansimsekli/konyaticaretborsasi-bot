from motor.motor_asyncio import AsyncIOMotorClient


class UserDatabase:
    CONNECTION_STRING: str

    def __init__(self, connection_string: str) -> None:
        self.CONNECTION_STRING = connection_string

    def __fetch_collection(self) -> AsyncIOMotorClient:
        client = AsyncIOMotorClient(self.CONNECTION_STRING)
        db = client["ktb-db"]
        collection = db["user_configs"]
        return collection

    async def new_user(self, user_id: int, first_name: str, last_name: str, dnd: bool = False):
        collection = self.__fetch_collection()
        user = {
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "dnd": dnd
        }
        await collection.insert_one(user)
        return user

    async def find(self, user_id: int) -> dict:
        collection = self.__fetch_collection()
        return await collection.find_one({'user_id': user_id})

    async def find_all(self, dnd: bool = False) -> list[int]:
        user_configs = self.__fetch_collection()
        users_cursor = user_configs.find({"dnd": dnd})
        user_list = await users_cursor.to_list(None)
        user_id_list = [user["user_id"] for user in user_list]
        return user_id_list

    async def toggle_notify_status(self, user_id: int) -> None:
        collection = self.__fetch_collection()
        await collection.find_one_and_update({'user_id': user_id},
                                             [{'$set': {'notify_status': {'$not': '$notify_status'}}}])
