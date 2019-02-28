from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DeleteView
from reversion.views import RevisionMixin

from crm.models import Attendance
from crm.views.mixin import UserManagerMixin


class Delete(LoginRequiredMixin, UserManagerMixin, RevisionMixin, DeleteView):
    model = Attendance
    template_name = 'crm/manager/attendance/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.subscription.restore_visit(self.object)
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('crm:manager:client:detail',
                       args=[self.object.client_id])
