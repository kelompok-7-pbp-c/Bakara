from django.urls import path

from . import api_views

app_name = 'authentication_api'

urlpatterns = [
    path('auth/csrf/', api_views.api_csrf, name='api_csrf'),
    path('auth/login/', api_views.api_login, name='api_login'),
    path('auth/register/', api_views.api_register, name='api_register'),
    path('auth/logout/', api_views.api_logout, name='api_logout'),
    path('auth/profile/', api_views.api_profile, name='api_profile'),
]
