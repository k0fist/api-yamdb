import re
import datetime

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(username):
    if username == settings.USER_ME:
        raise ValidationError(
            f'Имя пользователя "{username}" не поддерживается.'
        )
    invalid_chars = re.findall(r'[^\w.@+-]', username)
    if invalid_chars:
        unique_chars = ''.join(sorted(set(invalid_chars)))
        raise ValidationError(
            f'Поле username "{username}" содержит'
            f'недопустимые символы: {unique_chars}'
        )
    return username


def validate_year(year):
    current_year = datetime.datetime.now().year
    if year > current_year:
        raise ValidationError(
            f'Значение года {year} не может'
            f'превышать текущий год {current_year}.'
        )
    return year
