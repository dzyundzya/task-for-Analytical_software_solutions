from datetime import datetime

from src.models.schemas.base import BaseSchemaModel


class DocumentInCreate(BaseSchemaModel):
    """Схема входных данных для создания документа."""

    rubrics: list[str]
    text: str
    created_date: datetime


class DocumentInResponse(BaseSchemaModel):
    """ Схема ответа с данными документа."""

    id: int
    rubrics: list[str]
    text: str
    created_date: datetime
    updated_date: datetime | None
    is_deleted: bool
