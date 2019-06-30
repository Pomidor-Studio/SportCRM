from rest_framework.generics import CreateAPIView

from crm.serializers import RegisterCompanySerializer


class RegisterCompanyView(CreateAPIView):
    serializer_class = RegisterCompanySerializer
