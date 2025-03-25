from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    """Переопределение страндартной модели пользователя."""

    confirmation_code = models.TextField(
        'Код подтверждения',
        default=''
    )
