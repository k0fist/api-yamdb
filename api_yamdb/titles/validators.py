import re
from django.core.exceptions import ValidationError

REQUIRED_FIELD_PHRASE = 'Это поле обязательно для заполнения.'
USER_ME = 'me'


def validate_username(username):
    if username is None:
        raise ValidationError({'username': [REQUIRED_FIELD_PHRASE]})
    if username == USER_ME:
        raise ValidationError(
            {'username': ['Значение поля username: {username} недоступно']}
        )
    if not re.fullmatch(r'^[\w.@+-]+\Z', username):
        raise ValidationError(
            {'username': ['Поле username: {username} '
                          'имеет недопустимые символы']}
        )
