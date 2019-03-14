from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DeleteView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.models import Attendance


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = Attendance
    template_name = 'crm/manager/attendance/confirm_delete.html'
    permission_required = 'attendance.delete'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        self.object.subscription.restore_visit(self.object)
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', args=[
            self.object.event.event_class_id,
            self.object.event.date.year,
            self.object.event.date.month,
            self.object.event.date.day
        ])
