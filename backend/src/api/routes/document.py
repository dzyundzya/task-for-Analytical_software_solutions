from fastapi import APIRouter, Depends, File, Query, status, UploadFile, HTTPException

from src.api.dependencies.repository import get_repository
from src.models.enums.document import DocumentSort
from src.models.schemas.document import DocumentInCreate, DocumentInResponse, DocumentsListResponse
from src.repository.crud.document import DocumentCRUDRepository
from src.services.document.document_csv import DocumentCSVService
from src.services.document.document_el_search import DocumentSearchService
from src.utilities.exceptions.database import EntityDoesNotExist
from src.utilities.exceptions.http.exc_404 import http_404_exc_id_not_found_request

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    path="/import-csv",
    status_code=status.HTTP_201_CREATED,
)
async def import_documents_from_csv(
    csv_file: UploadFile = File(...),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> dict[str, int]:
    """Импортирует документы из CSV."""

    csv_service = DocumentCSVService(document_repo=document_repo)
    try:
        imported_count = await csv_service.import_documents_from_csv(
            csv_file=csv_file,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
    )
    total = await document_repo.count_documents(is_deleted=False)
    documents = await document_repo.read_documents(limit=total)

    async with DocumentSearchService() as search_service:
        indexed_count = await search_service.bulk_index_documents(
            documents=documents,
        )

    return {
        "imported_count": imported_count,
        "indexed_count": indexed_count,
    }


@router.post(
    path="/reindex",
    status_code=status.HTTP_200_OK,
)
async def reindex_documents(
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
) -> dict[str, int]:
    """Переиндексирует неудаленные документы в Elasticsearch."""

    total = await document_repo.count_documents(is_deleted=False)
    documents = await document_repo.read_documents(limit=total)

    async with DocumentSearchService() as search_service:
        indexed_count = await search_service.bulk_index_documents(
            documents=documents,
        )

    return {"indexed_count": indexed_count}


@router.post(
    path="",
    response_model=DocumentInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    document_create: DocumentInCreate,
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> DocumentInResponse:
    """Создает документ."""

    document = await document_repo.create_document(
        document_create=document_create,
    )

    # TODO: если бы не тестовое, вынес бы в scheduler
    # TODO: и тд. и тп.
    async with DocumentSearchService() as search_service:
        await search_service.bulk_index_documents(documents=[document])

    return DocumentInResponse.from_orm(document)


@router.get(
    path="",
    response_model=DocumentsListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_documents(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    sort: DocumentSort = Query(default=DocumentSort.CREATED_DATE_DESC),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> DocumentsListResponse:
    """Возвращает неудаленные документы."""

    documents = await document_repo.read_documents(
        limit=limit,
        offset=offset,
        sort=sort,
    )
    total = await document_repo.count_documents(is_deleted=False)

    items = [DocumentInResponse.from_orm(document) for document in documents]

    return DocumentsListResponse(
        items=items,
        limit=limit,
        offset=offset,
        count=len(items),
        total=total,
    )


@router.get(
    path="/search",
    response_model=DocumentsListResponse,
    status_code=status.HTTP_200_OK,
)
async def search_documents(
    query: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> DocumentsListResponse:
    """Ищет документы по тексту с помощью Elasticsearch."""

    async with DocumentSearchService() as search_service:
        search_result = await search_service.search_document_ids(
            text_query=query,
        )

    documents = await document_repo.read_documents_by_ids(
        document_ids=search_result.document_ids,
        limit=limit,
        offset=offset,
    )
    items = [DocumentInResponse.from_orm(document) for document in documents]

    return DocumentsListResponse(
        items=items,
        limit=limit,
        offset=offset,
        count=len(items),
        total=search_result.total,
    )


@router.get(
    path="/deleted",
    response_model=DocumentsListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_deleted_documents(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    sort: DocumentSort = Query(default=DocumentSort.UPDATED_DATE_DESC),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> DocumentsListResponse:
    """Возвращает is_deleted документы."""

    documents = await document_repo.read_deleted_documents(
        limit=limit,
        offset=offset,
        sort=sort,
    )
    total = await document_repo.count_documents(is_deleted=True)

    items = [DocumentInResponse.from_orm(document) for document in documents]

    return DocumentsListResponse(
        items=items,
        limit=limit,
        offset=offset,
        count=len(items),
        total=total,
    )


@router.get(
    path="/{document_id}",
    response_model=DocumentInResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document(
    document_id: int,
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> DocumentInResponse:
    """Возвращает неудаленный документ по pk."""

    try:
        document = await document_repo.read_document_by_id(
            pk=document_id,
        )
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(
            id=document_id,
        )

    return DocumentInResponse.from_orm(document)


@router.delete(
    path="/{document_id}",
    status_code=status.HTTP_200_OK,
)
async def soft_delete_document(
    document_id: int,
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> dict[str, str]:
    """Софтделит по pk."""

    try:
        result = await document_repo.soft_delete_document_by_id(
            pk=document_id,
        )
        async with DocumentSearchService() as search_service:
            is_delete_from_index = await search_service.delete_document(
                document_id=document_id,
            )
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(
            id=document_id,
        )

    return {
        "notification": result,
        "is_delete_from_index": str(is_delete_from_index),
    }


@router.delete(
    path="/{document_id}/hard",
    status_code=status.HTTP_200_OK,
)
async def hard_delete_document(
    document_id: int,
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    ),
) -> dict[str, str]:
    """Полное удаление из БД."""

    try:
        result = await document_repo.hard_delete_document_by_id(
            pk=document_id,
        )
        async with DocumentSearchService() as search_service:
            is_delete_from_index = await search_service.delete_document(
                document_id=document_id,
            )
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(
            id=document_id,
        )

    return {
        "notification": result,
        "is_delete_from_index": str(is_delete_from_index),
    }
