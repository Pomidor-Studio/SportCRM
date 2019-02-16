from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DeleteView

from crm.models import Attendance
from crm.views.mixin import UserManagerMixin


class Delete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    model = Attendance
    template_name = 'crm/manager/attendance/confirm_delete.html'

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.object.client_id])
