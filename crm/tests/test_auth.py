import itertools

import pytest
from django.core.exceptions import ValidationError

from hamcrest import assert_that, calling, raises

from crm.auth.password_validation import MinCharSetPresent


@pytest.mark.parametrize('password', [
    'aaaaaa',
    'AAAAAA',
    '111111',
    '%%%%%%'
])
def test_password_from_one_group(password):
    validator = MinCharSetPresent()

    assert_that(
        calling(validator.validate).with_args(password),
        raises(ValidationError)
    )


@pytest.mark.parametrize(
    'password',
    (''.join(x) for x in itertools.permutations('aA1!', 2))
)
def test_password_from_different_groups(password):
    validator = MinCharSetPresent()

    validator.validate(password)
