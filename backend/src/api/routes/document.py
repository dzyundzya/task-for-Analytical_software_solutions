from fastapi import APIRouter, Depends, UploadFile, File, Query, status

from src.api.dependencies.repository import get_repository
from src.models.enums.document import DocumentSort
from src.models.schemas.document import DocumentInResponse, DocumentInCreate, DocumentsListResponse
from src.repository.crud.document import DocumentCRUDRepository
from src.services.document_csv import DocumentCSVService
from src.utilities.exceptions.database import EntityDoesNotExist
from src.utilities.exceptions.http.exc_404 import http_404_exc_id_not_found_request


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    path='/import-csv',
    status_code=status.HTTP_201_CREATED,
)
async def import_documents_from_csv(
    csv_file: UploadFile = File(...),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
) -> dict[str, int]:
    """Импортирует документы из CSV."""

    csv_service = DocumentCSVService(document_repo=document_repo)
    imported_count = await csv_service.import_documents_from_csv(
        csv_file=csv_file,
    )

    return {"imported_count": imported_count}


@router.post(
    path="",
    response_model=DocumentInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    document_create: DocumentInCreate,
    document_repo: DocumentCRUDRepository  = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
) -> DocumentInResponse:
    """Создает документ."""

    document = await document_repo.create_document(
        document_create=document_create,
    )

    return DocumentInResponse.from_orm(document)


@router.get(
    path="",
    response_model=DocumentsListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_documents(
    limit:  int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    sort: DocumentSort = Query(default=DocumentSort.CREATED_DATE_DESC),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
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
    path='/deleted',
    response_model=DocumentsListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_deleted_documents(
    limit:  int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    sort: DocumentSort = Query(default=DocumentSort.UPDATED_DATE_DESC),
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
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
    path='/{document_id}',
    response_model=DocumentInResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document(
    document_id: int,
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
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
    path='/{document_id}',
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
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(
            id=document_id,
        )

    return {"notification": result}


@router.delete(
    path='/{document_id}/hard',
    status_code=status.HTTP_200_OK,
)
async def hard_delete_document(
    document_id: int,
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
) -> dict[str, str]:
    """Полное удаление из БД."""

    try:
        result = await document_repo.hard_delete_document_by_id(
            pk=document_id,
        )
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(
            id=document_id,
        )

    return {"notification": result}
