import logging
from datetime import timedelta
from django.utils import timezone
from .api import refresh_access_token

logger = logging.getLogger(__name__)

def refresh_expiring_allegro_tokens():
    """
    Znajduje i odświeża wszystkie tokeny Allegro, które wkrótce wygasną.
    """
    from .models import AllegroProfile 
    expiration_threshold = timezone.now() + timedelta(hours=1)
    profiles_to_refresh = AllegroProfile.objects.filter(
        refresh_token__isnull=False,
        token_expires_at__lte=expiration_threshold
    )

    logger.info(f"Znaleziono {profiles_to_refresh.count()} profili Allegro do odświeżenia.")

    for profile in profiles_to_refresh:
        logger.info(f"Próba odświeżenia tokenu dla użytkownika: {profile.user.username}")
        result = refresh_access_token(profile.refresh_token)
        if result["success"]:
            token_data = result["data"]
            profile.access_token = token_data['access_token']
            profile.refresh_token = token_data['refresh_token']
            expires_in = token_data['expires_in']
            profile.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            profile.save()
            logger.info(f"Pomyślnie odświeżono token dla: {profile.user.username}")
        else:
            logger.error(f"Błąd podczas odświeżania tokenu dla {profile.user.username}: {result['error']}")