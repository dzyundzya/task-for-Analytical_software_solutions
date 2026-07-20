from datetime import datetime

import sqlalchemy
from sqlalchemy.orm import (
    Mapped as SQLAlchemyMapped,
    mapped_column as sqlalchemy_mapped_column,
)
from sqlalchemy.sql import functions as sqlalchemy_function

from src.repository.table import Base


class Document(Base):
    """Сущность документов."""

    __tablename__ = "document"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    rubrics: SQLAlchemyMapped[list[str]] = sqlalchemy_mapped_column(
        sqlalchemy.ARRAY(sqlalchemy.String),
        nullable=False,
    )
    text: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.Text,
        nullable=False,
    )
    created_date: SQLAlchemyMapped[datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy_function.now(),
    )
    updated_date: SQLAlchemyMapped[datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        onupdate=sqlalchemy_function.now(),
    )
    is_deleted: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False,
        server_default=sqlalchemy.false(),
    )
