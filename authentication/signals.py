from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='authentication.User')
def create_user_profile(sender, instance, created, **kwargs):
    """
    Otomatis membuat Profile kosong setiap kali User baru dibuat,
    baik melalui registrasi manual maupun login SSO UI.

    Signal ini di-load oleh AuthenticationConfig.ready() di apps.py.
    Menggunakan string label 'authentication.User' sebagai sender agar
    aman dari circular import saat proses startup Django.
    """
    if created:
        from authentication.models import Profile
        Profile.objects.get_or_create(user=instance)
