import enum


class DocumentSort(str, enum.Enum):
    """Константы сортировки документов."""

    CREATED_DATE_DESC = "created_date_desc"
    CREATED_DATE_ASC = "created_date_asc"
    UPDATED_DATE_DESC = "updated_date_desc"
    UPDATED_DATE_ASC = "updated_date_asc"
