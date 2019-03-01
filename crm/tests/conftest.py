from pytest_factoryboy import register

from . import factories


register(factories.CompanyFactory)
register(factories.UserFactory)
register(factories.CoachFactory)
register(factories.ManagerFactory)
register(factories.LocationFactory)
register(factories.SubscriptionsTypeFactory)
register(factories.EventClassFactory)
register(factories.EventFactory)
register(factories.ClientFactory, 'client_model')
register(factories.ClientSubscriptionFactory)
