from typing import Sequence, cast

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.document import Document
from src.models.schemas.document import DocumentInCreate
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class DocumentCRUDRepository(BaseCRUDRepository):
    """Репозиторий для работы с документами."""

    async def create_document(self, document_create: DocumentInCreate) -> Document:
        """Создает документ в бд."""

        document = Document(**document_create.dict())

        self.async_session.add(instance=document)
        await self.async_session.commit()
        await self.async_session.refresh(instance=document)

        return document

    async def read_documents(self) -> Sequence[Document]:
        """Возвращает неудаленные документы."""

        documents_stmt = sqlalchemy.select(Document).where(
            Document.is_deleted.is_(False),
        ).order_by(Document.created_date.desc())

        query = await self.async_session.execute(statement=documents_stmt)
        return query.scalars().all()

    async def read_deleted_documents(self) -> Sequence[Document]:
        """Возвращает софт-удаленные документы."""

        documents_stmt = sqlalchemy.select(Document).where(
            Document.is_deleted.is_(True),
        ).order_by(Document.updated_date.desc())

        query = await self.async_session.execute(statement=documents_stmt)
        return query.scalars().all()

    async def read_document_by_id(self, pk: int) -> Document:
        """Возвращает неудаленный документ по pk."""

        document_stmt = sqlalchemy.select(Document).where(
            Document.id == pk,
            Document.is_deleted.is_(False),
        )

        query = await self.async_session.execute(statement=document_stmt)
        document = query.scalar_one_or_none()

        if document is None:
            raise EntityDoesNotExist(f'Документ с таким id: {pk} не существует.')

        return cast(Document, document)

    async def soft_delete_document_by_id(self, pk: int) -> str:
        """Мягкое удаление документа по pk."""

        document = await self.read_document_by_id(pk=pk)

        soft_delete_document_stmt = (
            sqlalchemy.update(table=Document)
            .where(Document.id == document.id)
            .values(
                is_deleted=True,
                updated_date=sqlalchemy_functions.now(),
            )
        )

        await self.async_session.execute(statement=soft_delete_document_stmt)
        await self.async_session.commit()

        return f"Документ с id: {pk} удален."

    async def hard_delete_document_by_id(self, pk: int) -> str:
        """Полное удаление документа из БД по pk."""

        document_stmt = sqlalchemy.select(Document).where(
            Document.id == pk,
            Document.is_deleted.is_(True),
        )

        query = await self.async_session.execute(statement=document_stmt)
        document = query.scalar_one_or_none()

        if document is None:
            raise EntityDoesNotExist(
                f"Документ с id: {pk} не существует или еще не удален."
            )

        hard_delete_document_stmt = sqlalchemy.delete(table=Document).where(
            Document.id == pk,
        )

        await self.async_session.execute(statement=hard_delete_document_stmt)
        await self.async_session.commit()

        return f"Документ с id: {pk} полностью удален из базы."
