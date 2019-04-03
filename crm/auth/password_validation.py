import string

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinCharSetPresent:
    def validate(self, password: str, user=None):
        lower = 0
        upper = 0
        digit = 0
        punctuation = 0
        for char in password:
            if char.islower():
                lower = 1
            elif char.isupper():
                upper = 1
            elif char.isdigit():
                digit = 1
            elif char in string.punctuation:
                punctuation = 1

        if lower + upper + digit + punctuation < 2:
            raise ValidationError(
                _("Password must have symbols from any two groups"),
                code='password_minimal_groups',
            )

    def get_help_text(self):
        return _("Your password can't be entirely from one type of symbols.")
