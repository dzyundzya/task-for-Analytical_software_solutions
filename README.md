# Document Search API

Тестовый backend-сервис на FastAPI для поиска по текстам документов.

Сервис хранит документы в PostgreSQL, индексирует текст в Elasticsearch и возвращает найденные документы со всеми полями из базы данных.

## Основа Проекта

Проект развернут на базе шаблона `Aeternalis-Ingenium/FastAPI-Backend-Template`.

В шаблоне уже были базовая структура FastAPI-приложения, подключение к PostgreSQL, SQLAlchemy async-слой, а также заготовки для аутентификации и авторизации. В рамках тестового задания поверх этого каркаса добавлены модель документов, CSV-импорт, интеграция с Elasticsearch, поиск и логика удаления документов.

## Что Реализовано
- PostgreSQL как основное хранилище документов.
- Elasticsearch как поисковый индекс по полю `text`.
- Импорт документов из CSV.
- Bulk insert документов в PostgreSQL.
- Автоматическая индексация в Elasticsearch после загрузки CSV.
- Поиск по произвольному текстовому запросу.
- Возврат первых документов с пагинацией и `total`.
- Сортировка документов по дате.
- Soft delete документа.
- Hard delete только для уже soft-deleted документов.
- Удаление документа из Elasticsearch при удалении через API.
- Ручная переиндексация Elasticsearch из PostgreSQL.
- Docker Compose для запуска PostgreSQL, Elasticsearch, Adminer и backend.
- OpenAPI-документация через FastAPI.

## Стек

- Python 3.11
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy Async ORM
- AsyncPG
- Elasticsearch
- Pydantic
- Docker Compose

## Модель Данных

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

PostgreSQL является источником истины. Elasticsearch используется только для поиска и может быть восстановлен из базы через ручку переиндексации.

## Как Работает Поиск

```text
1. Клиент отправляет GET /api/documents/search?query=...
2. Elasticsearch ищет совпадения по полю text.
3. Сервис получает id найденных документов.
4. PostgreSQL возвращает полные документы по этим id.
5. API возвращает документы с limit, offset, count и total.
```

## Быстрый Запуск

Скопировать переменные окружения:

```bash
cp .env.example .env
```

Запустить проект:

```bash
docker compose up --build
```

После запуска:

```text
Swagger UI:     http://localhost:8001/docs
OpenAPI JSON:  http://localhost:8001/openapi.json
Adminer:       http://localhost:8081
Elasticsearch: http://localhost:9200
```

Логи backend:

```bash
docker compose logs -f backend_app
```

Остановить контейнеры:

```bash
docker compose down
```

Остановить контейнеры и удалить данные volume:

```bash
docker compose down -v
```

## Переменные Окружения

Основные переменные описаны в `.env.example`.

Для запуска backend внутри Docker:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
ELASTICSEARCH_HOST=http://elasticsearch:9200
ELASTICSEARCH_DOCUMENT_INDEX=documents
ELASTICSEARCH_SEARCH_LIMIT=10000
```

Если backend запускается локально, а PostgreSQL и Elasticsearch остаются в Docker:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
ELASTICSEARCH_HOST=http://localhost:9200
```

## CSV Импорт

Файл должен содержать колонки:

```csv
text,created_date,rubrics
```

Пример `rubrics`:

```text
['VK-1603736028819866', 'VK-11879320040']
```

Импорт через API:

```text
POST /api/documents/import-csv
```

Ручка принимает файл через `multipart/form-data`.

После импорта сервис:

```text
1. читает CSV;
2. валидирует строки;
3. сохраняет документы в PostgreSQL через bulk insert;
4. индексирует документы в Elasticsearch;
5. возвращает количество импортированных и проиндексированных документов.
```

Пример ответа:

```json
{
  "imported_count": 1500,
  "indexed_count": 1500
}
```

## API

Создать документ:

```text
POST /api/documents
```

Получить неудаленные документы:

```text
GET /api/documents?limit=20&offset=0&sort=created_date_desc
```

Получить soft-deleted документы:

```text
GET /api/documents/deleted?limit=20&offset=0&sort=updated_date_desc
```

Получить документ по id:

```text
GET /api/documents/{document_id}
```

Поиск по тексту:

```text
GET /api/documents/search?query=конкурс&limit=20&offset=0
```

Soft delete:

```text
DELETE /api/documents/{document_id}
```

Hard delete:

```text
DELETE /api/documents/{document_id}/hard
```

Переиндексация Elasticsearch:

```text
POST /api/documents/reindex
```

## Формат Ответа Списка

```json
{
  "limit": 20,
  "offset": 0,
  "count": 20,
  "total": 42,
  "items": [
    {
      "id": 1,
      "rubrics": ["VK-1603736028819866"],
      "text": "Текст документа",
      "createdDate": "2019-05-31T17:18:42",
      "updatedDate": null,
      "isDeleted": false
    }
  ]
}
```

`total` показывает общее количество найденных или доступных документов. `count` показывает количество документов в текущем ответе.

## Удаление

Soft delete:

```text
is_deleted = true
```

При soft delete документ остается в PostgreSQL, исчезает из обычной выдачи и удаляется из Elasticsearch.

Hard delete физически удаляет документ из PostgreSQL, но только если документ уже был soft-deleted. Это снижает риск случайного полного удаления.

## OpenAPI

Swagger UI:

```text
http://localhost:8001/docs
```

OpenAPI JSON:

```text
http://localhost:8001/openapi.json
```

Сохранить OpenAPI в файл `docs.json`:

```bash
curl http://localhost:8001/openapi.json -o docs.json
```

## Проверка Работы

```text
1. Запустить docker compose up --build.
2. Открыть http://localhost:8001/docs.
3. Загрузить posts.csv через POST /api/documents/import-csv.
4. Проверить поиск через GET /api/documents/search?query=конкурс.
5. Удалить найденный документ через DELETE /api/documents/{document_id}.
6. Повторить поиск и убедиться, что удаленный документ не возвращается.
7. При необходимости выполнить POST /api/documents/reindex.
```

## Полезные Команды

Проверить Elasticsearch:

```bash
curl http://localhost:9200
```

Посмотреть количество документов в индексе:

```bash
curl http://localhost:9200/documents/_count
```

Запустить backend локально:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn src.main:backend_app --reload
```
