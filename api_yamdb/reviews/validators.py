import re
import datetime

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    if username == settings.USER_ME:
        raise ValidationError(
            {'Данное имя пользователя не поддерживается.'}
        )
    invalid_chars = ''.join(set(re.sub(r'[\w.@+-]', '', username)))
    if invalid_chars:
        raise ValidationError(
            f'Поле username содержит недопустимые символы: {invalid_chars}'
        )
    return username


def validate_year(value):
    current_year = datetime.datetime.now().year
    if value > current_year:
        raise ValidationError('Введите корректное значение года.')
