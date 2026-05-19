# 📰 MagNews Backend Documentation

Серверная часть маркетплейса подписок **MagNews**. Сейчас на витрине — журналы, газеты и научные журналы; архитектура каталога расширяется на цифровой контент.

REST API на **Python** с **FastAPI**, **SQLAlchemy** (ORM) и **PostgreSQL**.

## 🧩 Роли в системе

- **Подписчик (USER)** — оформляет и отменяет подписки, оставляет отзывы, подаёт жалобы.
- **Издатель (PROVIDER)** — регистрируется как поставщик контента, публикует издания, видит статус модерации.
- **Администратор (ADMIN)** — модерирует публикации, обрабатывает жалобы, блокирует подписки.

## 🛠 Технологический стек

- **Язык**: Python 3.10+
- **Фреймворк**: [FastAPI](https://fastapi.tiangolo.com/) (включая Uvicorn)
- **База данных**: PostgreSQL (psycopg2)
- **ORM**: SQLAlchemy 2.0
- **Миграции**: Alembic
- **Аутентификация**: JWT (python-jose, bcrypt, passlib)
- **Документация**: Sphinx + autodoc, OpenAPI/Swagger
- **Дополнительно**: eralchemy2 для ER-диаграммы.

---

## 🚀 Быстрый старт (Локальная разработка)

### 1. Клонирование репозитория

```bash
git clone https://github.com/DucZuyVuTM/MagNews-backend.git
cd MagNews-backend
```

### 2. Настройка окружения

```bash
python -m venv venv
source venv/bin/activate  # macOS / Linux
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 3. Переменные окружения

```bash
cp .env.example .env
# заполнить DATABASE_URL и SECRET_KEY
```

### 4. Миграции базы данных

```bash
DATABASE_URL=postgresql://... alembic upgrade head
```

### 5. Запуск приложения

```bash
uvicorn app.main:app --reload
```

Swagger UI — http://127.0.0.1:8000/docs

---

## 🐳 Docker

```bash
docker build -t magnews-backend .
docker run -p 8000:8000 --env-file .env magnews-backend
```

---

## 🗄 Uploads (cover images)

Обложки изданий хранятся в локальном файловом хранилище, смонтированном как Docker volume `magnews_uploads`.

- Эндпоинт загрузки: `POST /api/uploads/cover` (multipart, доступ — `PROVIDER` и `ADMIN`).
- Ограничения: JPEG / PNG / WebP, до 5 МБ.
- Раздача: статика по `/static/covers/{uuid}.{ext}`.
- Каталог внутри контейнера: `/app/uploads/covers/` (переопределяется через `UPLOAD_ROOT`).

Пример запуска с volume:

```bash
docker run -p 8000:8000 --env-file .env \
  -v magnews_uploads:/app/uploads \
  magnews-backend
```

## 📊 ERD

```bash
python gen_erd.py
```

Актуальная схема — `diagram.png`. Покрывает: User, Publication, Subscription, Complaint, Review.

## 🗂 Структура проекта

- `app/models.py` — доменные модели (User, Publication, Subscription, Complaint, Review).
- `app/routers/` — REST-эндпоинты (users, publications, subscriptions, complaints, reviews).
- `app/services/` — бизнес-логика, изолированная от транспорта.
- `alembic/` — миграции схемы данных.
- `tests/` — pytest, sqlite в файле для изоляции.
- `docs/` — Sphinx-документация (autodoc).
