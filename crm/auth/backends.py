from itertools import chain
from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from phonenumber_field.phonenumber import PhoneNumber

from crm.models import Coach, Manager

UserModel = get_user_model()


class ListUsersBackend(ModelBackend):
    def get_users_list(self, username) -> List:
        raise NotImplementedError()

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        users = self.get_users_list(username)

        if not users:
            UserModel().set_password(password)
            return

        # Try to login with one of matched users
        for user in users:
            if user.check_password(password) and \
                    self.user_can_authenticate(user):
                return user


class PhoneBackend(ListUsersBackend):
    def get_users_list(self, phone):
        if not phone:
            return []

        ph = PhoneNumber.from_string(phone)
        coachs = Coach.objects.filter(phone_number=ph)
        managers = Manager.objects.filter(phone_number=ph)
        return [x.user for x in chain(coachs, managers)]


class EmailBackend(ListUsersBackend):
    def get_users_list(self, email):
        return UserModel.objects.filter(email=email)
