from dataclasses import dataclass
from typing import Sequence

import pytest

from src.models.schemas.document import DocumentInCreate


class FakeDocumentRepository:
    """Фэйк репозитория для тестов документа."""

    def __init__(self) -> None:
        self.documents_create: list[DocumentInCreate] = []

    async def bulk_create_documents_form_scv(
            self,
            documents_create: Sequence[DocumentInCreate],
    ) -> int:
        self.documents_create = list(documents_create)
        return len(self.documents_create)


@dataclass
class FakeDocument:
    """Фэйк документов для тестов сервиса с Elasticsearch."""

    id: int
    text: str


@pytest.fixture
def fake_document_repo() -> FakeDocumentRepository:
    return FakeDocumentRepository()


@pytest.fixture
def fake_documents() -> list[FakeDocument]:
    return [
        FakeDocument(id=1, text="Тестовый 1"),
        FakeDocument(id=2, text="Тестовый 2"),
    ]
