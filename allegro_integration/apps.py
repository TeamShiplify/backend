import os
from django.apps import AppConfig

class AllegroIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'allegro_integration'

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from . import tasks
            print("Uruchamianie zadania odświeżania tokenów Allegro...")
            tasks.refresh_expiring_allegro_tokens()