# Foodgram - Продуктовый помощник

## 📦 Описание

**Foodgram** — это веб-приложение, позволяющее пользователям публиковать рецепты, добавлять рецепты в избранное, подписываться на других пользователей, формировать список покупок и многое другое.

---

## 🚀 Быстрый старт

Перед началом убедитесь, что на вашем компьютере установлен **Docker** и **Docker Compose**.

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/FS166/foodgram-st.git
cd foodgram-st/infna
```

### 2. Запустите проект в Docker

```bash
docker-compose up -d --build
```

Это соберёт и поднимет все необходимые контейнеры: backend, frontend и базу данных.

### 3. Загрузите ингредиенты

После запуска контейнеров обязательно загрузите список ингредиентов, чтобы тесты в Postman работали корректно:

```bash
docker-compose exec backend python manage.py load_ingredients
```

Если потребуется удалить загруженные ингредиенты, используйте:

```bash
docker-compose exec backend python manage.py delete_ingredients
```

---

## 🧪 Тестирование

Для корректного прохождения тестов в Postman убедитесь, что ингредиенты загружены.

---

## 🛠 Стек технологий

- Python / Django / Django REST Framework
- PostgreSQL
- Docker / Docker Compose
- Nginx
- Gunicorn
- Vue.js (frontend)

---

## 📂 Структура проекта

```bash
foodgram-st/
├── backend/         # Django backend
├── frontend/        # Сборка на Vue.js
├── docs/            # Документация (Postman и OpenAPI)
└── infna/           # docker-compose.yml и конфигурации
```

---

## 👨‍💻 Автор

Разработчик: [FS166](https://github.com/FS166)

---

## 📃 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](./LICENSE).
