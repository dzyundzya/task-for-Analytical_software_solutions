from datetime import datetime
from io import BytesIO

import pytest
from fastapi import UploadFile

from src.services.document.document_csv import DocumentCSVService


@pytest.mark.asyncio
async def test_import_documents_from_csv_parses_rows_and_bulk_creates_documents(
    fake_document_repo,
) -> None:
    """Проверяет парсинг CSV и передачу документов в bulk create."""

    csv_content = "text,created_date,rubrics\n" "\"Текст документа\",2024-01-01T12:30:00,\"['VK-1', 'VK-2']\"\n"
    csv_file = UploadFile(
        filename="posts.csv",
        file=BytesIO(csv_content.encode("utf-8")),
    )
    csv_service = DocumentCSVService(document_repo=fake_document_repo)

    imported_count = await csv_service.import_documents_from_csv(csv_file=csv_file)

    assert imported_count == 1
    assert len(fake_document_repo.documents_create) == 1

    document_create = fake_document_repo.documents_create[0]

    assert document_create.text == "Текст документа"
    assert document_create.rubrics == ["VK-1", "VK-2"]
    assert document_create.created_date == datetime(2024, 1, 1, 12, 30)


@pytest.mark.asyncio
async def test_import_documents_from_csv_rejects_not_csv_file(
    fake_document_repo,
) -> None:
    """Проверяет отказ от загрузки файла с другим расширением."""

    csv_file = UploadFile(
        filename="posts.txt",
        file=BytesIO(b""),
    )
    csv_service = DocumentCSVService(document_repo=fake_document_repo)

    with pytest.raises(ValueError, match="Загруженный файл должен быть CSV."):
        await csv_service.import_documents_from_csv(csv_file=csv_file)


@pytest.mark.asyncio
async def test_import_documents_from_csv_raises_error_for_invalid_row(
    fake_document_repo,
) -> None:
    """Проверяет ошибку при невалидной строке CSV."""

    csv_content = "text,created_date,rubrics\n" "\"Текст документа\",2024-01-01T12:30:00,\"['VK-1', 'VK-2'\"\n"
    csv_file = UploadFile(
        filename="posts.csv",
        file=BytesIO(csv_content.encode("utf-8")),
    )
    csv_service = DocumentCSVService(document_repo=fake_document_repo)

    with pytest.raises(SyntaxError):
        await csv_service.import_documents_from_csv(csv_file=csv_file)
