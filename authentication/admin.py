from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from authentication.models import Profile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'id', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'id')
    readonly_fields = ('id', 'date_joined', 'last_login')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'faculty', 'angkatan', 'whatsapp', 'line_id', 'updated_at')
    list_filter = ('faculty', 'angkatan')
    search_fields = ('user__username', 'user__email', 'full_name', 'whatsapp', 'line_id')
