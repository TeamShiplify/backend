import requests
import base64
import hashlib
import secrets
import string
from django.conf import settings
import uuid
ALLEGRO_API_URL = "https://api.allegro.pl.allegrosandbox.pl"

def get_user_orders(access_token: str):

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }

    endpoint = f"{ALLEGRO_API_URL}/order/events"
    
    try:
        response = requests.get(endpoint, headers=headers)

        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        error_message = f"Błąd API Allegro: {e}"
        if e.response is not None:
            error_message += f" | Treść błędu: {e.response.text}"
        return {"success": False, "error": error_message}
    
def refresh_access_token(refresh_token: str):

    try:
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        
        response = requests.post(
            settings.ALLEGRO_TOKEN_URL,
            data=data,
            auth=(settings.ALLEGRO_CLIENT_ID, settings.ALLEGRO_CLIENT_SECRET)
        )

        response.raise_for_status()

        return {"success": True, "data": response.json()}
        
    except requests.exceptions.RequestException as e:
        error_message = f"Błąd API Allegro podczas odświeżania tokenu: {e}"
        if e.response is not None:
            error_message += f" | Treść błędu: {e.response.text}"
        return {"success": False, "error": error_message}
    
def generate_pkce_codes():
    code_verifier = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    base64_encoded = base64.urlsafe_b64encode(hashed).decode('utf-8')
    code_challenge = base64_encoded.replace('=', '')
    return code_verifier, code_challenge

def exchange_code_for_token(code: str, code_verifier: str):
    try:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.ALLEGRO_REDIRECT_URI,
            'code_verifier': code_verifier,
        }
        response = requests.post(
            settings.ALLEGRO_TOKEN_URL,
            data=data,
            auth=(settings.ALLEGRO_CLIENT_ID, settings.ALLEGRO_CLIENT_SECRET)
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        error_message = f"Błąd API Allegro podczas wymiany kodu na token: {e}"
        if e.response is not None:
            error_message += f" | Treść błędu: {e.response.text}"
        return {"success": False, "error": error_message}
    
    
def get_checkout_form_details(access_token: str, checkout_form_id: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
    
    endpoint = f"{settings.ALLEGRO_API_URL}/order/checkout-forms/{checkout_form_id}"
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        error_message = f"Błąd API Allegro przy pobieraniu szczegółów zamówienia {checkout_form_id}: {e}"
        if e.response is not None:
            error_message += f" | Treść błędu: {e.response.text}"
        return {"success": False, "error": error_message}
    
def get_offer_details(access_token: str, offer_id: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
    endpoint = f"{settings.ALLEGRO_API_URL}/sale/offers/{offer_id}"
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    
    
def get_shipping_rates(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.allegro.public.v1+json"}
    endpoint = f"{settings.ALLEGRO_API_URL}/sale/shipping-rates"
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def search_categories(access_token: str, query: str):
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.allegro.public.v1+json"}
    endpoint = f"{settings.ALLEGRO_API_URL}/sale/categories?parent.id=root" # Wyszukujemy w głównych kategoriach
    params = {'name': query}
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_category_parameters(access_token: str, category_id: str):
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.allegro.public.v1+json"}
    endpoint = f"{settings.ALLEGRO_API_URL}/sale/categories/{category_id}/parameters"
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
        
def create_offer(access_token: str, offer_payload: dict):
    command_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "Content-Type": "application/vnd.allegro.public.v1+json",
    }
    endpoint = f"{settings.ALLEGRO_API_URL}/sale/offer-publication-commands/{command_id}"
    try:
        response = requests.put(endpoint, headers=headers, json=offer_payload)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        error_details = f"Błąd API: {e}"
        if e.response is not None:
            error_details += f" | Treść odpowiedzi: {e.response.text}"
        return {"success": False, "error": error_details}