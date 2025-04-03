# api_yamdb
api_yamdb - YaMDb собирает отзывы пользователей на различные произведения.

Авторы проекта:
1. [Сироткин Вадим](https://github.com/k0fist)
2. [Беседин Сергей](https://github.com/s-a-bes)

Алгоритм регистрации пользователей
1. Пользователь отправляет POST-запрос на добавление нового пользователя с параметрами email и username на эндпоинт /api/v1/auth/signup/.
2. YaMDB отправляет письмо с кодом подтверждения (confirmation_code) на адрес email.
3. Пользователь отправляет POST-запрос с параметрами username и confirmation_code на эндпоинт /api/v1/auth/token/, в ответе на запрос ему приходит token (JWT-токен).
4. При желании пользователь отправляет PATCH-запрос на эндпоинт /api/v1/users/me/ и заполняет поля в своём профайле (описание полей — в документации).

Все возможности API интерфейс веб-приложения yamdb описаны в документациипо эндпоинту: redoc/

## Техно-стек

- **Python 3.9** 
- **Django 5.1.1** 
- **Django REST Framework 3.15.2** 
- **Simple JWT** 
- **SQLite3** 
- **Requests 2.32.3** 
- **pytest 8.3.3** 
- **Flake8** 

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:{username}/api-yamdb.git
```

```
cd api_yamdb
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Импортировать данные:

```
python manage.py import_data
```

Запустить проект:

```
python manage.py runserver
```

После запуска полную документацию с примерами запросов можно посмотреть по адресу: http://127.0.0.1:8000/redoc/
