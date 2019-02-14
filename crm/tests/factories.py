import factory

from .. import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    first_name = factory.Faker('first_name', locale='ru')
    last_name = factory.Faker('last_name', locale='ru')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password',
                                                'defaultpassword')
