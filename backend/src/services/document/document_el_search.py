from dataclasses import dataclass
from typing import Sequence, cast, Any

import loguru
from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk

from src.config.manager import settings
from src.models.db.document import Document


@dataclass
class DocumentSearchResult:
    """Результат поиска доккументов в Elasticsearch."""

    document_ids: list[int]
    total: int


class DocumentSearchService:
    """Сервис интеграции документов с Elasticsearch."""

    def __init__(self) -> None:
        self._client = AsyncElasticsearch(hosts=[settings.ELASTICSEARCH_HOST])
        self._index_name = settings.ELASTICSEARCH_DOCUMENT_INDEX

    async def __aenter__(self) -> "DocumentSearchService":
        """Открывает контекстный менеджер."""

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрывает контекстный менеджер."""

        await self.close()

    async def close(self) -> None:
        """Закрывает соединение с Elasticsearch."""

        await self._client.close()

    async def create_index_if_not_exists(self) -> None:
        """Создает индекс документа, если он еще не существует."""

        is_index_exists = await self._client.indices.exists(index=self._index_name)

        if is_index_exists:
            return

        await self._client.indices.create(
            index=self._index_name,
            mappings={
                "properties": {
                    "id": {"type": "integer"},
                    "text": {"type": "text"},
                },
            },
        )

        loguru.logger.info(
            "ELASTIC_INDEX_CREATED | index={}",
            self._index_name,
        )

    async def bulk_index_documents(self, documents: Sequence[Document]) -> int:
        """Массово индексирует документы."""

        await self.create_index_if_not_exists()

        actions = [
            {
                "_op_type": "index",
                "_index": self._index_name,
                "_id": str(document.id),
                "_source": {
                    "id": document.id,
                    "text": document.text,
                },
            }
            for document in documents
        ]

        if not actions:
            return 0

        indexed_count, errors = await async_bulk(
            client=self._client,
            actions=actions,
            refresh=True,
            raise_on_error=False,
        )

        indexed_count = int(indexed_count)
        errors = cast(list[dict[str, Any]], errors)

        if errors:
            loguru.logger.error(
                "ELASTIC_BULK_INDEX_ERRORS | index={} | errors_count={}",
                self._index_name,
                len(errors),
            )
            raise RuntimeError("Не все документы удалось проиндексировать.")

        loguru.logger.info(
            "ELASTIC_BULK_INDEX_FINISHED | index={} | indexed_count={}",
            self._index_name,
            indexed_count,
        )

        return indexed_count

    async def search_document_ids(
        self,
        text_query: str,
    ) -> DocumentSearchResult:
        """Ищет документы по тексту и возвращает id найденных документов."""

        await self.create_index_if_not_exists()

        response = await self._client.search(
            index=self._index_name,
            size=settings.ELASTICSEARCH_SEARCH_LIMIT,
            query={
                "match": {
                    "text": text_query,
                },
            },
        )

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        return DocumentSearchResult(
            document_ids=[int(hit["_source"]["id"]) for hit in hits],
            total=int(total),
        )

    async def delete_document(self, document_id: int) -> bool:
        """Удаляет документ из поискового индекса."""

        await self.create_index_if_not_exists()

        try:
            await self._client.delete(
                index=self._index_name,
                id=str(document_id),
                refresh=True,
            )
        except NotFoundError:
            return False

        loguru.logger.info(
            "ELASTIC_DOCUMENT_DELETED | index={} | document_id={}",
            self._index_name,
            document_id,
        )

        return True
