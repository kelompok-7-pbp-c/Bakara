from django.urls import path
from authentication.views import register, login_user, login_sso, logout_user, edit_profile

app_name = 'authentication'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('login/sso/', login_sso, name='login_sso'),
    path('logout/', logout_user, name='logout'),
    path('profil/edit/', edit_profile, name='edit_profile'),
]
