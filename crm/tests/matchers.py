from django.http import HttpResponse
from hamcrest import has_property
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description


class DjangoResponse(BaseMatcher):

    def __init__(self, status_code):
        super().__init__()

        self.status_code = status_code

    def _matches(self, item):
        return (
            isinstance(item, HttpResponse) and
            has_property('status_code', self.status_code).matches(item)
        )

    def describe_to(self, description: Description):
        description.append_text(
            f'django response with status_code = {self.status_code}')


def is_http_200_response():
    return DjangoResponse(200)


def is_http_201_response():
    return DjangoResponse(201)


def is_http_204_response():
    return DjangoResponse(204)


def is_http_302_response():
    return DjangoResponse(302)


def is_http_404_response():
    return DjangoResponse(404)


def is_http_401_response():
    return DjangoResponse(401)


def is_http_400_response():
    return DjangoResponse(400)


def is_http_403_response():
    return DjangoResponse(403)
