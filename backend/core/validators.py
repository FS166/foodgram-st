import re
from django.core.exceptions import ValidationError


def validate_username(value):
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Имя пользователя может содержать \
            только буквы, цифры и символы @ . + - _'
        )
