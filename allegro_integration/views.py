from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode
from django.http import JsonResponse, HttpResponseBadRequest

from .models import AllegroProfile
from .processing import process_order_details
from django.shortcuts import render
from .forms import OfferCreateForm
from .api import get_shipping_rates, search_categories, get_category_parameters, create_offer
from .api import (
    get_user_orders, 
    refresh_access_token, 
    generate_pkce_codes, 
    exchange_code_for_token,
    get_checkout_form_details
)

@staff_member_required
def fetch_allegro_orders_view(request, user_id):
    """
    Widok wyzwalany przyciskiem w panelu admina.
    Pobiera zamówienia i wyświetla komunikat.
    """
    user = get_object_or_404(User, pk=user_id)
    
    try:

        access_token = user.allegro_profile.access_token
        if not access_token:
            messages.error(request, f"Brak tokenu Allegro dla użytkownika {user.username}.")
            return redirect('admin:auth_user_change', object_id=user_id)
            
    except User.allegro_profile.RelatedObjectDoesNotExist:
        messages.error(request, f"Brak profilu Allegro dla użytkownika {user.username}.")
        return redirect('admin:auth_user_change', object_id=user_id)

    result = get_user_orders(access_token)

    if result["success"]:
        orders_count = len(result["data"].get("events", []))
        messages.success(request, f"Pomyślnie pobrano {orders_count} zdarzeń zamówień dla {user.username}.")
        print(result["data"])
    else:
        messages.error(request, f"Nie udało się pobrać zamówień: {result['error']}")

    return redirect('admin:auth_user_change', object_id=user_id)

@staff_member_required
def refresh_allegro_token_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    try:
        profile = user.allegro_profile
        refresh_token = profile.refresh_token
        if not refresh_token:
            messages.error(request, f"Brak tokenu odświeżającego Allegro dla użytkownika {user.username}.")
            return redirect('admin:auth_user_change', object_id=user_id)
    except User.allegro_profile.RelatedObjectDoesNotExist:
        messages.error(request, f"Brak profilu Allegro dla użytkownika {user.username}.")
        return redirect('admin:auth_user_change', object_id=user_id)

    result = refresh_access_token(refresh_token)

    if result["success"]:
        token_data = result["data"]

        profile.access_token = token_data['access_token']
        profile.refresh_token = token_data['refresh_token']
        
        expires_in = token_data['expires_in']
        profile.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        profile.save()
        
        messages.success(request, f"Pomyślnie odświeżono token dla {user.username}.")
    else:
        messages.error(request, f"Nie udało się odświeżyć tokenu: {result['error']}")

    return redirect('admin:auth_user_change', object_id=user_id)

@staff_member_required
def initiate_allegro_auth_view(request, user_id):

    code_verifier, code_challenge = generate_pkce_codes()

    request.session['allegro_code_verifier'] = code_verifier
    request.session['allegro_user_id_for_auth'] = user_id

    auth_url_base = "https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize"
    params = {
        'response_type': 'code',
        'client_id': settings.ALLEGRO_CLIENT_ID,
        'redirect_uri': settings.ALLEGRO_REDIRECT_URI,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge,
    }
    return redirect(f"{auth_url_base}?{urlencode(params)}")

@staff_member_required
def allegro_oauth_callback_view(request):
    authorization_code = request.GET.get('code')
    if not authorization_code:
        messages.error(request, "Autoryzacja nie powiodła się: brak kodu autoryzacyjnego w odpowiedzi od Allegro.")
        return redirect('admin:index')

    code_verifier = request.session.pop('allegro_code_verifier', None)
    user_id = request.session.pop('allegro_user_id_for_auth', None)

    if not code_verifier or not user_id:
        messages.error(request, "Błąd sesji. Spróbuj ponownie rozpocząć proces autoryzacji.")
        return redirect('admin:index')

    result = exchange_code_for_token(authorization_code, code_verifier)
    user = get_object_or_404(User, pk=user_id)

    if result["success"]:
        token_data = result["data"]
        profile, _ = AllegroProfile.objects.get_or_create(user=user)
        profile.access_token = token_data['access_token']
        profile.refresh_token = token_data['refresh_token']
        expires_in = token_data['expires_in']
        profile.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        profile.save()
        messages.success(request, f"Pomyślnie połączono konto Allegro dla użytkownika {user.username}.")
    else:
        messages.error(request, f"Nie udało się uzyskać tokenów: {result['error']}")

    return redirect('admin:auth_user_change', object_id=user_id)


@staff_member_required
def process_allegro_orders_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    try:
        access_token = user.allegro_profile.access_token
        if not access_token:
            messages.error(request, "Brak tokenu Allegro dla tego użytkownika.")
            return redirect('admin:auth_user_change', object_id=user_id)
    except User.allegro_profile.RelatedObjectDoesNotExist:
        messages.error(request, "Brak profilu Allegro dla tego użytkownika.")
        return redirect('admin:auth_user_change', object_id=user_id)

    events_result = get_user_orders(access_token)
    if not events_result['success']:
        messages.error(request, f"Błąd pobierania listy zdarzeń: {events_result['error']}")
        return redirect('admin:auth_user_change', object_id=user_id)

    created_count = 0
    updated_count = 0
    failed_ids = []

    events = events_result['data'].get('events', [])

    for event in events:
        checkout_form_id = event['order']['checkoutForm']['id']

        details_result = get_checkout_form_details(access_token, checkout_form_id)
        
        if details_result['success']:

            _, created = process_order_details(user, access_token, details_result['data'])
            if created:
                created_count += 1
            else:
                updated_count += 1
        else:
            failed_ids.append(checkout_form_id)
            messages.warning(request, f"Nie udało się pobrać szczegółów dla {checkout_form_id}: {details_result['error']}")

    messages.success(request, f"Przetwarzanie zakończone. Utworzono: {created_count}, zaktualizowano: {updated_count} zamówień.")
    if failed_ids:
        messages.error(request, f"Liczba zamówień, których nie udało się przetworzyć: {len(failed_ids)}.")

    return redirect('admin:allegro_integration_order_changelist')

@staff_member_required
def create_offer_view(request):

    user = request.user 
    access_token = user.allegro_profile.access_token

    shipping_rates_result = get_shipping_rates(access_token)
    shipping_rates_choices = []
    if shipping_rates_result['success']:
        shipping_rates_choices = [(rate['id'], rate['name']) for rate in shipping_rates_result['data']['shippingRates']]

    if request.method == 'POST':
        form = OfferCreateForm(request.POST, shipping_rates_choices=shipping_rates_choices)
        if form.is_valid():
            try:
                payload = form.structure_payload()

                dynamic_params = []
                for key, value in request.POST.items():
                    if key.startswith('param_'):
                        param_id = key.split('_')[1]
                        if ':' in value:
                            value_id, _ = value.split(':', 1)
                            dynamic_params.append({"id": param_id, "valuesIds": [value_id]})
                        else:
                            dynamic_params.append({"id": param_id, "values": [value]})
                
                payload['parameters'] = dynamic_params
                
                # Wyślij do API
                result = create_offer(access_token, payload)
                
                if result['success']:
                    messages.success(request, f"Pomyślnie wysłano żądanie wystawienia oferty. ID zadania: {result['data']['id']}")
                    return redirect('admin:index')
                else:
                    messages.error(request, f"Błąd wystawiania oferty: {result['error']}")

            except ValueError as e:
                messages.error(request, f"Błąd walidacji: {e}")
    else:
        form = OfferCreateForm(shipping_rates_choices=shipping_rates_choices)
        
    context = {
        'form': form,
        'title': 'Wystaw nową ofertę',
        'has_permission': True,
    }
    return render(request, 'admin/allegro_integration/create_offer.html', context)

@staff_member_required
def search_category_api_view(request):
    query = request.GET.get('query', '')
    if len(query) < 2:
        return JsonResponse({'error': 'Query too short'}, status=400)
    
    access_token = request.user.allegro_profile.access_token
    result = search_categories(access_token, query)
    
    if result['success']:
        return JsonResponse(result['data'])
    return JsonResponse({'error': result['error']}, status=500)

@staff_member_required
def get_category_parameters_api_view(request, category_id):
    access_token = request.user.allegro_profile.access_token
    result = get_category_parameters(access_token, category_id)

    if result['success']:
        return JsonResponse(result['data'])
    return JsonResponse({'error': result['error']}, status=500)