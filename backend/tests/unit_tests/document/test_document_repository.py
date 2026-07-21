import pytest

from src.models.enums.document import DocumentSort
from src.repository.crud.document import DocumentCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist
from tests.unit_tests.document.factories import (
    build_document,
    build_document_create,
    FakeAsyncSession,
    FakeQueryResult,
)


@pytest.mark.asyncio
async def test_count_documents_returns_documents_count() -> None:
    """Проверяет возврат количества документов."""

    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalar_one_value=2),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    documents_count = await repo.count_documents(is_deleted=False)

    assert documents_count == 2


@pytest.mark.asyncio
async def test_create_document_adds_document_and_commits() -> None:
    """Проверяет создание документа с commit и refresh."""

    session = FakeAsyncSession()
    repo = DocumentCRUDRepository(async_session=session)

    document = await repo.create_document(document_create=build_document_create())

    assert document.text == "Тестовый документ"
    assert session.added_instance is document
    assert session.refreshed_instance is document
    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_create_document_rollbacks_on_commit_error() -> None:
    """Проверяет rollback при ошибке commit во время создания документа."""

    session = FakeAsyncSession(commit_error=RuntimeError("db error"))
    repo = DocumentCRUDRepository(async_session=session)

    with pytest.raises(RuntimeError, match="db error"):
        await repo.create_document(document_create=build_document_create())

    assert session.rollback_count == 1


@pytest.mark.asyncio
async def test_read_documents_returns_not_deleted_documents() -> None:
    """Проверяет получение неудаленных документов."""

    document = build_document()
    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalars_all_value=[document]),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    documents = await repo.read_documents(
        limit=20,
        offset=0,
        sort=DocumentSort.CREATED_DATE_DESC,
    )

    assert documents == [document]


@pytest.mark.asyncio
async def test_read_deleted_documents_returns_deleted_documents() -> None:
    """Проверяет получение soft-deleted документов."""

    document = build_document(is_deleted=True)
    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalars_all_value=[document]),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    documents = await repo.read_deleted_documents(
        limit=20,
        offset=0,
        sort=DocumentSort.UPDATED_DATE_DESC,
    )

    assert documents == [document]


@pytest.mark.asyncio
async def test_read_document_by_id_returns_document() -> None:
    """Проверяет получение неудаленного документа по id."""

    document = build_document()
    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalar_one_or_none_value=document),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    found_document = await repo.read_document_by_id(pk=1)

    assert found_document is document


@pytest.mark.asyncio
async def test_read_document_by_id_raises_error_when_document_not_found() -> None:
    """Проверяет ошибку, если документ по id не найден."""

    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalar_one_or_none_value=None),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    with pytest.raises(EntityDoesNotExist):
        await repo.read_document_by_id(pk=1)


@pytest.mark.asyncio
async def test_soft_delete_document_by_id_updates_document() -> None:
    """Проверяет мягкое удаление документа."""

    document = build_document()
    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalar_one_or_none_value=document),
            FakeQueryResult(),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    result = await repo.soft_delete_document_by_id(pk=1)

    assert result == "Документ с id: 1 удален."
    assert session.execute_count == 2
    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_hard_delete_document_by_id_deletes_soft_deleted_document() -> None:
    """Проверяет полное удаление soft-deleted документа."""

    document = build_document(is_deleted=True)
    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalar_one_or_none_value=document),
            FakeQueryResult(),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    result = await repo.hard_delete_document_by_id(pk=1)

    assert result == "Документ с id: 1 полностью удален из базы."
    assert session.execute_count == 2
    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_hard_delete_document_by_id_raises_error_when_document_not_deleted() -> None:
    """Проверяет ошибку hard delete для отсутствующего или неудаленного документа."""

    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(scalar_one_or_none_value=None),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    with pytest.raises(EntityDoesNotExist):
        await repo.hard_delete_document_by_id(pk=1)


@pytest.mark.asyncio
async def test_bulk_create_documents_form_scv_returns_zero_for_empty_list() -> None:
    """Проверяет, что bulk create не ходит в БД для пустого списка."""

    session = FakeAsyncSession()
    repo = DocumentCRUDRepository(async_session=session)

    created_count = await repo.bulk_create_documents_form_scv(documents_create=[])

    assert created_count == 0
    assert session.execute_count == 0


@pytest.mark.asyncio
async def test_bulk_create_documents_form_scv_creates_documents() -> None:
    """Проверяет массовое создание документов."""

    session = FakeAsyncSession(
        execute_results=[
            FakeQueryResult(),
        ],
    )
    repo = DocumentCRUDRepository(async_session=session)

    created_count = await repo.bulk_create_documents_form_scv(
        documents_create=[build_document_create()],
    )

    assert created_count == 1
    assert session.execute_count == 1
    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_read_documents_by_ids_returns_empty_list_for_empty_ids() -> None:
    """Проверяет быстрый возврат пустого списка без запроса в БД."""

    session = FakeAsyncSession()
    repo = DocumentCRUDRepository(async_session=session)

    documents = await repo.read_documents_by_ids(document_ids=[])

    assert documents == []
    assert session.execute_count == 0
