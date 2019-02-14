import factory

from .. import models


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Faker('pystr', min_chars=20, max_chars=30)
    first_name = factory.Faker('first_name', locale='ru')
    last_name = factory.Faker('last_name', locale='ru')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password',
                                                'defaultpassword')


class CoachFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Coach

    user = factory.SubFactory(UserFactory)


class ManagerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Manager

    user = factory.SubFactory(UserFactory)
