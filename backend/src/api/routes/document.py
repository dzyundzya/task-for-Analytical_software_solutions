from fastapi import APIRouter, Depends, status

from src.api.dependencies.repository import get_repository
from src.models.schemas.document import DocumentInResponse, DocumentInCreate
from src.repository.crud.document import DocumentCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist
from src.utilities.exceptions.http.exc_404 import http_404_exc_id_not_found_request


router = APIRouter(prefix="/documents", tags=["documents"])


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
    response_model=list[DocumentInResponse],
    status_code=status.HTTP_200_OK,
)
async def get_documents(
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
) -> list[DocumentInResponse]:
    """Возвращает неудаленные документы."""

    documents = await document_repo.read_documents()

    return [DocumentInResponse.from_orm(document) for document in documents]


@router.get(
    path='/deleted',
    response_model=list[DocumentInResponse],
    status_code=status.HTTP_200_OK,
)
async def get_deleted_documents(
    document_repo: DocumentCRUDRepository = Depends(
        get_repository(repo_type=DocumentCRUDRepository),
    )
) -> list[DocumentInResponse]:
    """Возвращает is_deleted документы."""

    documents = await document_repo.read_deleted_documents()

    return [DocumentInResponse.from_orm(document) for document in documents]


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


