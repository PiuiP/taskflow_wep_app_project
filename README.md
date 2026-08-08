## О проекте

TaskFlow — это проект, родившийся из реальной потребности: существующие инструменты (Trello, Jira, Moodle) либо слишком тяжеловесны для маленькой учебной группы, либо не учитывают её специфику.

Приложение закрывает базовый цикл взаимодействия **«преподаватель ↔ студент»**:
- преподаватель создаёт задание, прикрепляет файл условия и назначает его конкретным студентам;
- студент видит только свои задачи, загружает решение и отслеживает прогресс;
- администратор управляет пользователями и ролями.

Никакой лишней функциональности. Только то, что действительно нужно.

---

## Возможности

### Преподаватель
-  Дашборд группы с круговой диаграммой статусов и таблицей успеваемости
-  Создание заданий с дедлайном, описанием и файлом условия
-  Массовое назначение заданий студентам своей группы
-  Проверка работ: быстрая смена статуса или детальная проверка с оценкой и комментарием
-  Просмотр индивидуальной успеваемости любого студента группы

### Студент
-  Список только своих задач с фильтрацией по статусу
-  Цветовая индикация просроченных заданий
-  Загрузка файлов решений
-  Личная страница успеваемости со средним баллом и историей оценок
-  Просмотр комментариев преподавателя к работам

###  Администратор
-  Управление пользователями (создание, редактирование, удаление)
-  Смена ролей и учебных групп
-  Фильтрация по ролям с пагинацией

---

##  Технологический стек

| Слой | Технологии |
|------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Frontend** | Jinja2, Bootstrap 5 |
| **База данных** | PostgreSQL 16 |
| **Аутентификация** | JWT (python-jose), bcrypt, httpOnly cookies |
| **Инфраструктура** | Docker, Docker Compose |

---

## Структура проекта

```
taskflow/
├── app/
│   ├── main.py              # Точка входа, композиция модулей
│   ├── config.py            # Валидация переменных окружения
│   ├── database.py          # SQLAlchemy engine и сессии
│   ├── models.py            # ORM-модели (User, Task, Assignment, Comment, File)
│   ├── auth.py              # JWT, bcrypt, фабрика require_role
│   ├── middleware.py        # Глобальная аутентификация
│   ├── dependencies.py      # Общие зависимости (templates)
│   ├── utils.py             # Валидация типов файлов
│   ├── routers/             # Маршруты по ролям
│   │   ├── auth.py          # /login, /register, /logout
│   │   ├── teacher.py       # /teacher/*
│   │   ├── student.py       # /student/*
│   │   ├── admin.py         # /admin/*
│   │   └── files.py         # /download/{file_id}
│   └── templates/           # Jinja2-шаблоны
├── scripts/
│   └── seed.py              # Инициализация БД тестовыми данными
├── uploads/                 # Загруженные пользователями файлы
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Быстрый старт

### Локальный запуск

1. **Клонируй репозиторий:**
   ```bash
   git clone https://github.com/PiuiP/taskflow_wep_app_project.git
   cd taskflow_wep_app_project
   ```

2. **Создай виртуальное окружение:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate     # Windows
   ```

3. **Установи зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запусти PostgreSQL в Docker:**
   ```bash
   docker run --name taskflow_pg \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres123 \
     -e POSTGRES_DB=taskflow \
     -p 5433:5432 -d postgres:16
   ```

5. **Создай файл `.env`**:
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5433
   POSTGRES_DB=taskflow
   POSTGRES_DB_USER=postgres
   POSTGRES_DB_PASSWORD=postgres123
   SECRET_KEY=your-super-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

6. **Инициализируй БД тестовыми данными:**
   ```bash
   python -m scripts.seed
   ```

7. **Запусти приложение:**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Открой в браузере:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Запуск через Docker Compose

```bash
docker-compose up --build
```
---

## Тестовые учётные записи

| Роль | Логин | Пароль |
|------|-------|--------|
| Администратор | `admin` | `admin123` |
| Преподаватель | `teacher` | `teacher123` |
| Студент 1 | `student1` | `student123` |
| Студент 2 | `student2` | `student123` |

---

## Безопасность

- Пароли хешируются алгоритмом **bcrypt** с адаптивной сложностью
- JWT-токены хранятся в **httpOnly cookies**
- Серверная валидация типов загружаемых файлов по белому списку (`.pdf`, `.docx`, `.txt`)
- Уникальные имена файлов через UUID

---

## Roadmap

- [ ] Модуль email-уведомлений о новых заданиях
- [ ] Поддержка нескольких групп у одного преподавателя
- [ ] Экспорт статистики в PDF/Excel
- [x] Unit-тесты 
---

MIT © [Алина Минок](https://github.com/PiuiP)

---
