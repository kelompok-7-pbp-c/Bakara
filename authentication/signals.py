from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='authentication.User')
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        from authentication.models import Profile
        Profile.objects.get_or_create(user=instance)
