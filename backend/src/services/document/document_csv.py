import ast
import csv
import io
from datetime import datetime

import loguru
from fastapi import UploadFile

from src.models.schemas.document import DocumentInCreate
from src.repository.crud.document import DocumentCRUDRepository


class DocumentCSVService:
    """Сервис интеграции документов из CSV."""

    def __init__(self, document_repo: DocumentCRUDRepository) -> None:
        self._document_repo = document_repo

    async def import_documents_from_csv(self, csv_file: UploadFile) -> int:
        """Импортирует документ из CSV в БД."""

        loguru.logger.info("CSV_IMPORT_START | filename={}", csv_file.filename)

        if not csv_file.filename or not csv_file.filename.endswith(".csv"):
            raise ValueError("Загруженный файл должен быть CSV.")

        content = await csv_file.read()
        text_stream = io.StringIO(content.decode("utf-8"))
        reader = csv.DictReader(text_stream)

        documents_create: list[DocumentInCreate] = []

        for row_number, row in enumerate(reader, 2):
            try:
                documents_create.append(
                    DocumentInCreate(
                        rubrics=ast.literal_eval(row["rubrics"]),
                        text=row["text"],
                        created_date=datetime.fromisoformat(row["created_date"]),
                    )
                )
            except Exception:
                loguru.logger.exception(
                    "CSV_IMPORT_ROW_PARSE_FAILED | filename={} | row_number={}",
                    csv_file.filename,
                    row_number,
                )
                raise

        imported_count: int = await self._document_repo.bulk_create_documents_form_scv(
            documents_create=documents_create,
        )

        loguru.logger.info(
            "CSV_IMPORT_FINISHED | filename={} | imported_count={}",
            csv_file.filename,
            imported_count,
        )

        return imported_count
