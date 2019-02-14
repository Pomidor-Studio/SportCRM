from pytest_factoryboy import register

from . import factories


register(factories.UserFactory)
register(factories.CoachFactory)
register(factories.ManagerFactory)
