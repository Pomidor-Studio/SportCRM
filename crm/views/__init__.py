from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from ..forms import (
    ClientSubscriptionForm, EventClassForm, ExtendClientSubscriptionForm,
)
from ..models import (
    Attendance, ClientSubscriptions, EventClass,
)


def ExtendSubscription(request, pk=None):
    if request.method == 'POST':
        print(request.POST)
        ClientSubscriptions.objects.get(
            pk=request.POST['object_id']
        ).extend_duration(request.POST['visit_limit'])
        return HttpResponseRedirect(
            reverse(
                'crm:manager:client:detail',
                args=[request.POST['client_id']]
            )
        )
    else:
        subscription = ClientSubscriptions.objects.get(pk=pk)
        form = ExtendClientSubscriptionForm(subscription=subscription)
    return render(request, 'crm/extend_subscription.html', {'form': form})


class ClientSubscriptionUpdateView(UpdateView):
    model = ClientSubscriptions
    form_class = ClientSubscriptionForm


class ClientSubscriptionDeleteView(DeleteView):
    model = ClientSubscriptions

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.object.client.id, ])


class AttendanceDelete(DeleteView):
    model = Attendance
    template_name = "crm/common_confirm_delete.html"

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.object.client_id, ])
