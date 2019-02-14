from django.contrib.auth.mixins import UserPassesTestMixin


class UserManagerMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_manager


class UserCoachMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_coach
