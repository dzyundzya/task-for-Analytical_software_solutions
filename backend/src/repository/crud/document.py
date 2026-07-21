from typing import Sequence, cast

import loguru
import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.enums.document import DocumentSort
from src.models.db.document import Document
from src.models.schemas.document import DocumentInCreate
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist

_DOCUMENT_SORT_COLUMNS = {
    DocumentSort.CREATED_DATE_DESC: Document.created_date.desc(),
    DocumentSort.CREATED_DATE_ASC: Document.created_date.asc(),
    DocumentSort.UPDATED_DATE_DESC: Document.updated_date.desc(),
    DocumentSort.UPDATED_DATE_ASC: Document.updated_date.asc(),
}


class DocumentCRUDRepository(BaseCRUDRepository):
    """Репозиторий для работы с документами."""

    async def count_documents(self, is_deleted: bool = False) -> int:
        """Возвращает количество документов."""

        documents_count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count()).select_from(Document).where(Document.is_deleted.is_(is_deleted))
        )

        query = await self.async_session.execute(statement=documents_count_stmt)
        return int(query.scalar_one())

    async def create_document(self, document_create: DocumentInCreate) -> Document:
        """Создает документ в бд."""

        document = Document(**document_create.dict())

        try:
            self.async_session.add(instance=document)
            await self.async_session.commit()
            await self.async_session.refresh(instance=document)
        except Exception:
            await self.async_session.rollback()
            raise

        return document

    async def read_documents(
        self,
        limit: int = 20,
        offset: int = 0,
        sort: DocumentSort = DocumentSort.CREATED_DATE_DESC,
    ) -> Sequence[Document]:
        """Возвращает неудаленные документы."""

        documents_stmt = (
            sqlalchemy.select(Document)
            .where(
                Document.is_deleted.is_(False),
            )
            .order_by(_DOCUMENT_SORT_COLUMNS[sort])
            .limit(limit)
            .offset(offset)
        )

        query = await self.async_session.execute(statement=documents_stmt)
        return query.scalars().all()

    async def read_deleted_documents(
        self,
        limit: int = 20,
        offset: int = 0,
        sort: DocumentSort = DocumentSort.UPDATED_DATE_DESC,
    ) -> Sequence[Document]:
        """Возвращает софт-удаленные документы."""

        documents_stmt = (
            sqlalchemy.select(Document)
            .where(
                Document.is_deleted.is_(True),
            )
            .order_by(_DOCUMENT_SORT_COLUMNS[sort])
            .limit(limit)
            .offset(offset)
        )

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
            raise EntityDoesNotExist(f"Документ с таким id: {pk} не существует.")

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

        try:
            await self.async_session.execute(statement=soft_delete_document_stmt)
            await self.async_session.commit()
        except Exception:
            await self.async_session.rollback()
            raise

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
            raise EntityDoesNotExist(f"Документ с id: {pk} не существует или еще не удален.")

        hard_delete_document_stmt = sqlalchemy.delete(table=Document).where(
            Document.id == pk,
        )

        try:
            await self.async_session.execute(statement=hard_delete_document_stmt)
            await self.async_session.commit()
        except Exception:
            await self.async_session.rollback()
            raise

        loguru.logger.warning(
            "HARD_DELETE_DOCUMENT | document_id={}",
            pk,
        )

        return f"Документ с id: {pk} полностью удален из базы."

    async def bulk_create_documents_form_scv(
        self,
        documents_create: Sequence[DocumentInCreate],
    ) -> int:
        """Массовое создание документов для интеграции из CSV."""

        if not documents_create:
            return 0
        try:
            await self.async_session.execute(
                sqlalchemy.insert(table=Document),
                [document_create.dict() for document_create in documents_create],
            )
            await self.async_session.commit()
        except Exception:
            await self.async_session.rollback()
            raise

        return len(documents_create)

    async def read_documents_by_ids(
        self,
        document_ids: Sequence[int],
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Document]:
        """Возвращает неудаленные документы из list[id]."""

        if not document_ids:
            return []

        documents_stmt = (
            sqlalchemy.select(Document)
            .where(
                Document.id.in_(document_ids),
                Document.is_deleted.is_(False),
            )
            .order_by(Document.created_date.desc())
            .limit(limit)
            .offset(offset)
        )

        query = await self.async_session.execute(statement=documents_stmt)

        return query.scalars().all()
