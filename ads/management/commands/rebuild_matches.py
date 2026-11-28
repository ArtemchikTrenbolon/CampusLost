from django.core.management.base import BaseCommand

from ads.matching import update_matches
from ads.models import Ad


class Command(BaseCommand):
    help = 'Пересчитывает совпадения для всех активных объявлений'

    def handle(self, *args, **options):
        total = 0
        for ad in Ad.objects.filter(status=Ad.Status.ACTIVE):
            total += len(update_matches(ad))
        self.stdout.write(self.style.SUCCESS(f'Создано новых совпадений: {total}'))