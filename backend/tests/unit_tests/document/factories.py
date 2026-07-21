from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from src.models.db.document import Document
from src.models.schemas.document import DocumentInCreate


@dataclass
class FakeDocument:
    """Фэйк документа для тестов сервиса с Elasticsearch."""

    id: int
    text: str


class FakeDocumentRepository:
    """Фэйк репозитория для тестов документа."""

    def __init__(self) -> None:
        self.documents_create: list[DocumentInCreate] = []

    async def bulk_create_documents_form_scv(
        self,
        documents_create: Sequence[DocumentInCreate],
    ) -> int:
        """Сохраняет документы в память вместо БД."""

        self.documents_create = list(documents_create)
        return len(self.documents_create)


class FakeScalars:
    """Фэйк результата scalars() SQLAlchemy."""

    def __init__(self, items: list[Document]) -> None:
        self._items = items

    def all(self) -> list[Document]:
        """Возвращает список документов."""

        return self._items


class FakeQueryResult:
    """Фэйк результата выполнения SQLAlchemy-запроса."""

    def __init__(
        self,
        scalar_one_value: int | None = None,
        scalar_one_or_none_value: Document | None = None,
        scalars_all_value: list[Document] | None = None,
    ) -> None:
        self._scalar_one_value = scalar_one_value
        self._scalar_one_or_none_value = scalar_one_or_none_value
        self._scalars_all_value = scalars_all_value or []

    def scalar_one(self) -> int:
        """Возвращает одиночное scalar-значение."""

        return int(self._scalar_one_value)

    def scalar_one_or_none(self) -> Document | None:
        """Возвращает один документ или None."""

        return self._scalar_one_or_none_value

    def scalars(self) -> FakeScalars:
        """Возвращает фэйк коллекции scalar-значений."""

        return FakeScalars(items=self._scalars_all_value)


class FakeAsyncSession:
    """Фэйк асинхронной SQLAlchemy-сессии."""

    def __init__(
        self,
        execute_results: list[Any] | None = None,
        commit_error: Exception | None = None,
    ) -> None:
        self.execute_results = execute_results or []
        self.commit_error = commit_error
        self.added_instance: Document | None = None
        self.refreshed_instance: Document | None = None
        self.execute_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def add(self, instance: Document) -> None:
        """Запоминает добавленную модель."""

        self.added_instance = instance

    async def execute(self, statement: Any = None, *args: Any, **kwargs: Any) -> Any:
        """Возвращает заранее подготовленный результат запроса."""

        self.execute_count += 1

        result = self.execute_results.pop(0)

        if isinstance(result, Exception):
            raise result

        return result

    async def commit(self) -> None:
        """Фиксирует commit или выбрасывает подготовленную ошибку."""

        self.commit_count += 1

        if self.commit_error:
            raise self.commit_error

    async def rollback(self) -> None:
        """Фиксирует вызов rollback."""

        self.rollback_count += 1

    async def refresh(self, instance: Document) -> None:
        """Запоминает обновленную модель."""

        self.refreshed_instance = instance


def build_document(is_deleted: bool = False) -> Document:
    """Создает тестовую модель документа."""

    return Document(
        id=1,
        rubrics=["VK-1"],
        text="Тестовый документ",
        created_date=datetime(2024, 1, 1, 12, 30),
        is_deleted=is_deleted,
    )


def build_document_create() -> DocumentInCreate:
    """Создает тестовую схему для создания документа."""

    return DocumentInCreate(
        rubrics=["VK-1"],
        text="Тестовый документ",
        created_date=datetime(2024, 1, 1, 12, 30),
    )
