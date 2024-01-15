from typing import TypeVar, List, Optional, Union, Generic, get_args
from uuid import UUID

from sqlalchemy import insert, exc, select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Query, selectinload

ModelType = TypeVar("ModelType")
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


class BaseManager(Generic[ModelType, CreateSchema, UpdateSchema]):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._model: ModelType = get_args(self.__orig_bases__[0])[0]

    async def create(self, obj_in: CreateSchema) -> ModelType:
        query = insert(self._model).values(**obj_in.dict()).returning(self._model)
        result = await self._session.execute(query)
        obj = result.scalar_one()
        return obj

    async def create_multi(self, objs_in: List[CreateSchema]) -> List[ModelType]:
        objs: List[ModelType] = []
        for obj_in in objs_in:
            query = insert(self._model).values(**obj_in.dict()).returning(self._model)
            result = await self._session.execute(query)
            obj = result.scalar_one()
            objs.append(obj)
        return objs

    async def get(
            self, obj_id: Union[int, str, UUID], relationships: List[relationship] = None
    ) -> Optional[ModelType]:
        query = self._build_query(relationships).filter(
            self._model.id == obj_id
        )
        try:
            result = await self._session.execute(query)
            return result.scalar_one()
        except exc.NoResultFound:
            return None

    async def get_by_unique_value(
            self, relationships: List[relationship] = None, **kwargs
    ) -> Optional[ModelType]:
        query = self._build_query(relationships).filter_by(
            **kwargs
        )
        try:
            result = await self._session.execute(query)
            return result.scalar_one()
        except exc.NoResultFound:
            return None
        except exc.MultipleResultsFound:
            result = await self._session.scalars(query)
            return result.first()

    async def get_multi(
            self, skip: int = 0, limit: Optional[int] = None, relationships: List[relationship] = None, **kwargs
    ) -> List[ModelType]:
        if limit is None:
            query = self._build_query(relationships).offset(skip)
        else:
            query = self._build_query(relationships).offset(skip).limit(limit)
        query = query.filter_by(
            **kwargs
        )
        result = await self._session.scalars(query)
        return list(result.all())

    async def update(self, obj_id: Union[int, str, UUID], obj_in: UpdateSchema) -> None:
        stmt = update(self._model).where(self._model.id == obj_id).values(**obj_in.dict(exclude_unset=True))
        await self._session.execute(stmt)
        return None

    async def delete(self, obj_id: Union[int, str, UUID]) -> None:
        query = delete(self._model).where(self._model.id == obj_id)
        await self._session.execute(query)
        return None

    async def delete_multi(self, objs_id: List[Union[int, str, UUID]]) -> None:
        query = delete(self._model).where(self._model.id.in_(objs_id))
        await self._session.execute(query)

    async def get_count(self, **kwargs) -> int:
        query = select(func.count(self._model.id)).filter_by(**kwargs)
        count = await self._session.execute(query)
        return count.scalar_one()

    def _build_query(
            self, relationships: Union[List[relationship], relationship] = None
    ) -> Query:
        query = select(self._model)
        if relationships is not None:
            if isinstance(relationships, list):
                for model_relationship in relationships:
                    query = query.options(
                        selectinload(model_relationship)
                    )
            else:
                query = query.options(
                    selectinload(relationships)
                )
        return query
