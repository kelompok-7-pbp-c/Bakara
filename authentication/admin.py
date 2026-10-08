from django.contrib import admin

from authentication.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'faculty', 'angkatan', 'whatsapp', 'line_id', 'updated_at')
    list_filter = ('faculty', 'angkatan')
    search_fields = ('user__username', 'user__email', 'full_name', 'whatsapp', 'line_id')
