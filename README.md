# Document Search API

Тестовый backend-сервис на FastAPI для поиска по текстам документов.

Документы хранятся в PostgreSQL, а поисковый индекс строится в Elasticsearch. PostgreSQL является основным источником данных, Elasticsearch используется только для текстового поиска.

## Основа

Проект развернут на базе шаблона `Aeternalis-Ingenium/FastAPI-Backend-Template`.

В шаблоне уже были базовая структура FastAPI-приложения, подключение к PostgreSQL, async SQLAlchemy, а также заготовки аутентификации и авторизации. В рамках тестового задания добавлены документы, CSV-импорт, Elasticsearch, поиск, удаление и тесты бизнес-логики.

## Реализовано

- PostgreSQL для хранения документов.
- Elasticsearch для поиска по полю `text`.
- Импорт документов из CSV.
- Bulk insert документов в БД.
- Автоматическая индексация после CSV-импорта.
- Поиск по произвольному текстовому запросу.
- Возврат документов с `limit`, `offset`, `count`, `total`.
- Сортировка по дате создания и обновления.
- Soft delete и hard delete.
- Удаление документа из индекса при удалении через API.
- Ручная переиндексация Elasticsearch из PostgreSQL.
- Docker Compose.
- OpenAPI-документация.

## Стек

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy Async ORM
- AsyncPG
- Elasticsearch
- Pydantic
- Docker Compose
- Pytest

## Данные

Документ в PostgreSQL:

```text
id
rubrics
text
created_date
updated_date
is_deleted
```

Документ в Elasticsearch:

```text
id
text
```

Поиск работает по схеме:

```text
Elasticsearch ищет по text -> сервис получает id -> PostgreSQL возвращает полные документы
```

## Файлы Для Проверки

- `docs.json` сформирован и находится в корне проекта.
- CSV-файл из тестового задания находится в `backend/dumps/posts.csv`.

## Запуск В Docker

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

```text
Swagger UI:     http://localhost:8001/docs
OpenAPI JSON:  http://localhost:8001/openapi.json
Adminer:       http://localhost:8081
Elasticsearch: http://localhost:9200
```

Основные переменные для Docker:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
ELASTICSEARCH_HOST=http://elasticsearch:9200
ELASTICSEARCH_DOCUMENT_INDEX=documents
ELASTICSEARCH_SEARCH_LIMIT=10000
```

## Локальный Запуск

Локально обычно запускается только backend, а PostgreSQL и Elasticsearch остаются в Docker.

Сначала поднять инфраструктуру:

```bash
docker compose up -d db elasticsearch db_editor
```

В `.env` для локального backend нужно заменить host/port:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
ELASTICSEARCH_HOST=http://localhost:9200
```

После этого запустить backend:

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn src.main:backend_app --reload
```

Локально backend будет доступен по адресу:

```text
http://127.0.0.1:8000/docs
```

Для возврата к Docker-запуску backend нужно вернуть:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
ELASTICSEARCH_HOST=http://elasticsearch:9200
```

## CSV

Файл должен содержать колонки:

```csv
text,created_date,rubrics
```

Пример `rubrics`:

```text
['VK-1603736028819866', 'VK-11879320040']
```

Импорт:

```text
POST /api/documents/import-csv
```

Ручка принимает файл через `multipart/form-data`, сохраняет документы в PostgreSQL через bulk insert и индексирует их в Elasticsearch.

Пример ответа:

```json
{
  "imported_count": 1500,
  "indexed_count": 1500
}
```

## API

```text
POST   /api/documents
GET    /api/documents?limit=20&offset=0&sort=created_date_desc
GET    /api/documents/search?query=конкурс&limit=20&offset=0
GET    /api/documents/deleted?limit=20&offset=0&sort=updated_date_desc
GET    /api/documents/{document_id}
DELETE /api/documents/{document_id}
DELETE /api/documents/{document_id}/hard
POST   /api/documents/reindex
```

Формат ответа списка:

```json
{
  "limit": 20,
  "offset": 0,
  "count": 20,
  "total": 42,
  "items": []
}
```

Soft delete помечает документ как `is_deleted = true` и удаляет его из Elasticsearch. Hard delete физически удаляет документ из PostgreSQL только после soft delete.

## Тесты

Добавлены минимальные unit-тесты бизнес-логики. Вручную покрыты:

- CSV-сервис;
- Elasticsearch-сервис;
- репозиторий документов.

Тесты используют fake-объекты и `monkeypatch`, без поднятия реальных PostgreSQL и Elasticsearch.

```bash
cd backend
pytest tests/unit_tests/document -q -n 0
```

## OpenAPI

Swagger UI:

```text
http://localhost:8001/docs
```

Сохранить OpenAPI в файл `docs.json`:

```bash
curl http://localhost:8001/openapi.json -o docs.json
```

## Проверка

```text
1. Запустить docker compose up --build.
2. Открыть http://localhost:8001/docs.
3. Загрузить posts.csv через POST /api/documents/import-csv.
4. Проверить поиск через GET /api/documents/search?query=конкурс.
5. Удалить найденный документ через DELETE /api/documents/{document_id}.
6. Повторить поиск и убедиться, что документ не возвращается.
```

Полезные команды:

```bash
docker compose logs -f backend_app
curl http://localhost:9200
curl http://localhost:9200/documents/_count
docker compose down
```
