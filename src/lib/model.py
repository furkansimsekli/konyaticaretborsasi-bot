from datetime import datetime


class MongoModel:
    collection = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.created_at = kwargs.get('created_at', datetime.now())

    def to_dict(self):
        return self.__dict__

    async def save(self, query: dict = None):
        if self.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        if query is None:
            query = {"_id": getattr(self, "_id", None)}

        existing_document = await self.collection.find_one(query)
        if existing_document:
            await self.collection.update_one(query, {"$set": self.to_dict()})
        else:
            await self.collection.insert_one(self.to_dict())

    @classmethod
    def initialize_collection(cls, db, collection_name: str):
        cls.collection = db[collection_name]

    @classmethod
    async def find_one(cls, query: dict):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        document = await cls.collection.find_one(query)
        if document:
            return cls(**document)
        return None

    @classmethod
    async def find_all(cls, query: dict = None, sort: list = None):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        query = query or {}
        cursor = cls.collection.find(query)

        if sort:
            cursor = cursor.sort(sort)

        documents = []
        async for document in cursor:
            documents.append(cls(**document))
        return documents

    @classmethod
    async def fetch_paginated(cls, query: dict = None, skip: int = 0, limit: int = 10, sort: list = None):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        query = query or {}
        cursor = cls.collection.find(query).skip(skip).limit(limit)

        if sort:
            cursor = cursor.sort(sort)

        documents = []
        async for document in cursor:
            documents.append(cls(**document))
        return documents

    @classmethod
    async def update(cls, query: dict, update_data: dict):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        result = await cls.collection.update_one(query, {"$set": update_data})
        return result.modified_count

    @classmethod
    async def update_many(cls, query: dict, update_data: dict):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        result = await cls.collection.update_many(query, {"$set": update_data})
        return result.modified_count

    @classmethod
    async def delete(cls, query: dict):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        result = await cls.collection.delete_one(query)
        return result.deleted_count > 0

    @classmethod
    async def delete_many(cls, query: dict):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        result = await cls.collection.delete_many(query)
        return result.deleted_count

    @classmethod
    async def count(cls, query: dict = None):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        query = query or {}
        count = await cls.collection.count_documents(query)
        return count

    @classmethod
    async def aggregate(cls, pipeline: list):
        if cls.collection is None:
            raise ValueError("Collection is not initialized. Call 'initialize_collection' first.")

        cursor = cls.collection.aggregate(pipeline)
        results = []
        async for document in cursor:
            results.append(document)
        return results
