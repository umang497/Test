from string import ascii_letters, digits

from django.core.exceptions import ValidationError


def validate_positive(number):
    if number <= 0:
        raise ValidationError("This number should be more than 0.")


def validate_non_negative(number):
    if number < 0:
        raise ValidationError("This number should not be negative.")


def validate_alphanumeric(string: str):
    ascii_letters_set = frozenset(ascii_letters + digits)
    if not ascii_letters_set.issuperset(string):
        raise ValidationError('Enter a valid alphanumeric string.')


def validate_spaced_alphanumeric(string: str):
    allowed_special_characters = ' '
    ascii_letters_set = frozenset(ascii_letters + digits + allowed_special_characters)
    if not ascii_letters_set.issuperset(string):
        raise ValidationError('Enter a valid alphanumeric string.')
