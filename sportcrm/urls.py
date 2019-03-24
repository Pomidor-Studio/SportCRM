"""sportcrm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.conf import settings

app_name = 'sportcrm'
if not settings.BACKGROUND_MODE:
    urlpatterns = [
        path('admin/', admin.site.urls, name='admin'),
        path('', include('crm.urls')),
        path('', include('bot.urls')),
        path('', include('social_django.urls', namespace='social')),
        path(
            'api/v1/',
            include(('crm.urls_api', 'api-v1'), namespace='api-v1')
        ),
        path(
            'api/v1/',
            include(('bot.urls_api', 'bot-api-v1'), namespace='bot-api-v1')
        ),
        path(
            'qr_code/',
            include(('qr_code.urls', 'qr_code'), namespace="qr_code")
        ),
        path('', include('vk_group_app.urls')),
    ]
else:
    urlpatterns = [
        path('', include('google_tasks.urls')),
    ]
