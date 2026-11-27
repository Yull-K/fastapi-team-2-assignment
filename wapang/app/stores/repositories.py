from typing import Annotated
import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from wapang.app.stores.models import Store
from wapang.app.items.models import Item
from wapang.database.connection import get_db_session
    
class StoreRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_db_session)]) -> None:
        self.session = session

    async def create_store(
            self, 
            user_id: str,
            store_name: str,
            address: str,
            email: str,
            phone_number: str,
            delivery_fee: int
        ) -> Store:
        store = Store(user_id=user_id,store_name = store_name,address=address,email=email,phone_number=phone_number,delivery_fee=delivery_fee)
        self.session.add(store)
        await self.session.flush()
        
        return store

    async def update_store(
            self, 
            store: Store,
            store_name: str | None,
            address: str | None,
            email: str | None,
            phone_number: str | None,
            delivery_fee: int | None
        ) -> Store:

        if store_name is not None:
            store.store_name = store_name
        if address is not None:
            store.address = address
        if email is not None:
            store.email = email
        if phone_number is not None:
            store.phone_number = phone_number
        if delivery_fee is not None:
            store.delivery_fee = delivery_fee

        await self.session.flush()

        return store
    
    # 한 사용자는 최대 하나의 상점만 소유할 수 있습니다.
    async def get_store_by_user_id(self, user_id: str) -> Store | None:
        return await self.session.scalar(select(Store).where(Store.user_id == user_id))

    # store_name: 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
    async def get_store_by_name(self, store_name: str) -> Store | None:
        return await self.session.scalar(select(Store).where(Store.store_name == store_name))

    # email: 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
    async def get_store_by_email(self, email: str) -> Store | None:
        return await self.session.scalar(select(Store).where(Store.email == email))

    # phone_number: 기존에 존재하는 상점과 중복되지 않는지 확인해야 합니다.
    async def get_store_by_phone_number(self, phone_number: str) -> Store | None:
        return await self.session.scalar(select(Store).where(Store.phone_number == phone_number))
    
    # 각 상점에는 고유 식별자로 id(str)가 부여됩니다.
    async def get_store_by_id(self, store_id: str) -> Store | None:
        return await self.session.scalar(select(Store).where(Store.id == store_id))
    
    # store.items로 그냥 읽으면 지연로딩이 막혀 MissingGreenlet에러가 발생하기 때문
    # Item을 비동기로 직접 쿼리로 가져오는 메서드를 추가.
    async def get_items_by_store_id(self, store_id:str) -> list[Item]:
        result = await self.session.scalars(select(Item).where(Item.store_id == store_id))
        return list(result.all())

    