from collections.abc import Sequence

import pytest

from src.services.document import document_el_search
from src.services.document.document_el_search import DocumentSearchService


def build_search_service_without_real_client() -> DocumentSearchService:
    """Создает сервис без реального подключения к Elasticsearch."""

    search_service = object.__new__(DocumentSearchService)
    search_service._client = object()
    search_service._index_name = "documents"

    return search_service


@pytest.mark.asyncio
async def test_bulk_index_documents_builds_elasticsearch_actions(
    fake_documents,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет формирование bulk actions для Elasticsearch."""

    captured_actions: list[dict] = []
    search_service = build_search_service_without_real_client()

    async def fake_create_index_if_not_exists() -> None:
        return None

    async def fake_async_bulk(
        client: object,
        actions: Sequence[dict],
        refresh: bool,
        raise_on_error: bool,
    ) -> tuple[int, list[dict]]:
        captured_actions.extend(actions)
        return len(captured_actions), []

    monkeypatch.setattr(
        search_service,
        "create_index_if_not_exists",
        fake_create_index_if_not_exists,
    )
    monkeypatch.setattr(document_el_search, "async_bulk", fake_async_bulk)

    indexed_count = await search_service.bulk_index_documents(documents=fake_documents)

    assert indexed_count == 2
    assert captured_actions == [
        {
            "_op_type": "index",
            "_index": "documents",
            "_id": "1",
            "_source": {
                "id": 1,
                "text": "Тестовый 1",
            },
        },
        {
            "_op_type": "index",
            "_index": "documents",
            "_id": "2",
            "_source": {
                "id": 2,
                "text": "Тестовый 2",
            },
        },
    ]


@pytest.mark.asyncio
async def test_bulk_index_documents_returns_zero_for_empty_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет нулевой результат для пустого списка документов."""

    search_service = build_search_service_without_real_client()

    async def fake_create_index_if_not_exists() -> None:
        return None

    monkeypatch.setattr(
        search_service,
        "create_index_if_not_exists",
        fake_create_index_if_not_exists,
    )

    indexed_count = await search_service.bulk_index_documents(documents=[])

    assert indexed_count == 0


@pytest.mark.asyncio
async def test_bulk_index_documents_raises_runtime_error_when_elastic_returns_errors(
    fake_documents,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет ошибку при неуспешной bulk-индексации."""

    search_service = build_search_service_without_real_client()

    async def fake_create_index_if_not_exists() -> None:
        return None

    async def fake_async_bulk(
        client: object,
        actions: Sequence[dict],
        refresh: bool,
        raise_on_error: bool,
    ) -> tuple[int, list[dict]]:
        return 1, [{"index": {"error": "test error"}}]

    monkeypatch.setattr(
        search_service,
        "create_index_if_not_exists",
        fake_create_index_if_not_exists,
    )
    monkeypatch.setattr(document_el_search, "async_bulk", fake_async_bulk)

    with pytest.raises(RuntimeError, match="Не все документы удалось проиндексировать."):
        await search_service.bulk_index_documents(documents=fake_documents)


@pytest.mark.asyncio
async def test_search_document_ids_returns_ids_and_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет возврат id документов и total из Elasticsearch."""

    class FakeElasticClient:
        async def search(self, **kwargs) -> dict:
            return {
                "hits": {
                    "total": {"value": 2},
                    "hits": [
                        {"_source": {"id": 10}},
                        {"_source": {"id": 20}},
                    ],
                },
            }

    search_service = build_search_service_without_real_client()
    search_service._client = FakeElasticClient()

    async def fake_create_index_if_not_exists() -> None:
        return None

    monkeypatch.setattr(
        search_service,
        "create_index_if_not_exists",
        fake_create_index_if_not_exists,
    )

    search_result = await search_service.search_document_ids(text_query="конкурс")

    assert search_result.document_ids == [10, 20]
    assert search_result.total == 2


@pytest.mark.asyncio
async def test_delete_document_returns_true_when_document_deleted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет успешное удаление документа из индекса."""

    class FakeElasticClient:
        def __init__(self) -> None:
            self.delete_kwargs: dict | None = None

        async def delete(self, **kwargs) -> None:
            self.delete_kwargs = kwargs

    search_service = build_search_service_without_real_client()
    fake_client = FakeElasticClient()
    search_service._client = fake_client

    async def fake_create_index_if_not_exists() -> None:
        return None

    monkeypatch.setattr(
        search_service,
        "create_index_if_not_exists",
        fake_create_index_if_not_exists,
    )

    is_deleted = await search_service.delete_document(document_id=123)

    assert is_deleted is True
    assert fake_client.delete_kwargs == {
        "index": "documents",
        "id": "123",
        "refresh": True,
    }


@pytest.mark.asyncio
async def test_delete_document_returns_false_when_document_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет False, если документа нет в индексе."""

    class FakeNotFoundError(Exception):
        pass

    class FakeElasticClient:
        async def delete(self, **kwargs) -> None:
            raise FakeNotFoundError

    search_service = build_search_service_without_real_client()
    search_service._client = FakeElasticClient()

    async def fake_create_index_if_not_exists() -> None:
        return None

    monkeypatch.setattr(
        search_service,
        "create_index_if_not_exists",
        fake_create_index_if_not_exists,
    )
    monkeypatch.setattr(document_el_search, "NotFoundError", FakeNotFoundError)

    is_deleted = await search_service.delete_document(document_id=123)

    assert is_deleted is False


@pytest.mark.asyncio
async def test_create_index_if_not_exists_does_not_create_existing_index() -> None:
    """Проверяет пропуск создания уже существующего индекса."""

    class FakeIndices:
        def __init__(self) -> None:
            self.is_create_called = False

        async def exists(self, index: str) -> bool:
            return True

        async def create(self, **kwargs) -> None:
            self.is_create_called = True

    class FakeElasticClient:
        def __init__(self) -> None:
            self.indices = FakeIndices()

    search_service = build_search_service_without_real_client()
    search_service._client = FakeElasticClient()

    await search_service.create_index_if_not_exists()

    assert search_service._client.indices.is_create_called is False


@pytest.mark.asyncio
async def test_create_index_if_not_exists_creates_missing_index() -> None:
    """Проверяет создание отсутствующего индекса."""

    class FakeIndices:
        def __init__(self) -> None:
            self.create_kwargs: dict | None = None

        async def exists(self, index: str) -> bool:
            return False

        async def create(self, **kwargs) -> None:
            self.create_kwargs = kwargs

    class FakeElasticClient:
        def __init__(self) -> None:
            self.indices = FakeIndices()

    search_service = build_search_service_without_real_client()
    search_service._client = FakeElasticClient()

    await search_service.create_index_if_not_exists()

    assert search_service._client.indices.create_kwargs == {
        "index": "documents",
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "text": {"type": "text"},
            },
        },
    }


@pytest.mark.asyncio
async def test_search_service_context_manager_closes_client() -> None:
    """Проверяет закрытие Elasticsearch-клиента в контекстном менеджере."""

    class FakeElasticClient:
        def __init__(self) -> None:
            self.is_closed = False

        async def close(self) -> None:
            self.is_closed = True

    search_service = build_search_service_without_real_client()
    fake_client = FakeElasticClient()
    search_service._client = fake_client

    async with search_service as opened_search_service:
        assert opened_search_service is search_service
        assert fake_client.is_closed is False

    assert fake_client.is_closed is True
