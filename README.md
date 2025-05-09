# Foodgram 

## Старт

Перед началом убедитесь, что на вашем компьютере установлен **Docker** и **Docker Compose**.

### 0. Клонируйте репозиторий

```bash
git clone https://github.com/FS166/foodgram-st.git
cd foodgram-st/infna
```

### 1. Переименуйте .env.example -> .env и добавьте свои данные в .env

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

Документация доступна по адресу:
```bash
api/docs/
```