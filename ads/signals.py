from django.db.models.signals import post_save
from django.dispatch import receiver

from .matching import update_matches
from .models import Ad


@receiver(post_save, sender=Ad)
def find_matches_on_save(sender, instance, **kwargs):
    update_matches(instance)