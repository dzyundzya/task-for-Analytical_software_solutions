import pytest

from tests.unit_tests.document.factories import FakeDocument, FakeDocumentRepository


@pytest.fixture
def fake_document_repo() -> FakeDocumentRepository:
    """Возвращает фэйк репозитория документов."""

    return FakeDocumentRepository()


@pytest.fixture
def fake_documents() -> list[FakeDocument]:
    """Возвращает фэйк документы для Elasticsearch-тестов."""

    return [
        FakeDocument(id=1, text="Тестовый 1"),
        FakeDocument(id=2, text="Тестовый 2"),
    ]
