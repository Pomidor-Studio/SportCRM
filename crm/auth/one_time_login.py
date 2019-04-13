import sesame.utils
from django.urls import reverse


def get_one_time_login_link(host, user):
    return '{host}{url}{qs}'.format(
        host=host,
        url=reverse('crm:accounts:profile'),
        qs=sesame.utils.get_query_string(user)
    )
