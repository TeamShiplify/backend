from django.core.management.base import BaseCommand
from allegro_integration.tasks import refresh_expiring_allegro_tokens

class Command(BaseCommand):
    help = 'Odświeża tokeny Allegro, które wkrótce wygasną.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Rozpoczynanie procesu odświeżania tokenów Allegro...'))
        refresh_expiring_allegro_tokens()
        self.stdout.write(self.style.SUCCESS('Proces odświeżania tokenów zakończony.'))