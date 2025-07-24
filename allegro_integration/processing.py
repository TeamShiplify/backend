from decimal import Decimal
from django.utils.dateparse import parse_datetime
from .models import Client, Order, LineItem
from .api import get_offer_details

def process_order_details(user, access_token: str, data: dict):

    buyer_data = data['buyer']
    client, _ = Client.objects.update_or_create(
        allegro_id=buyer_data['id'],
        defaults={
            'login': buyer_data['login'],
            'email': buyer_data['email'],
            'first_name': buyer_data['firstName'],
            'last_name': buyer_data['lastName'],
            'phone_number': buyer_data.get('phoneNumber'),
        }
    )

    delivery_data = data['delivery']
    payment_data = data.get('payment')
    order_defaults = {
        'user': user,
        'buyer': client,
        'status': data['status'],
        'allegro_updated_at': parse_datetime(data['updatedAt']),
        'delivery_method_name': delivery_data['method']['name'],
        'delivery_cost': Decimal(delivery_data['cost']['amount']),
        'delivery_street': delivery_data['address']['street'],
        'delivery_city': delivery_data['address']['city'],
        'delivery_post_code': delivery_data['address']['zipCode'],
        'delivery_country_code': delivery_data['address']['countryCode'],
        'payment_id': payment_data.get('id') if payment_data else None,
        'payment_type': payment_data.get('type') if payment_data else None,
        'total_to_pay': Decimal(data['summary']['totalToPay']['amount']),
    }
    order, created = Order.objects.update_or_create(
        checkout_form_id=data['id'],
        defaults=order_defaults
    )
    

    for item_data in data['lineItems']:

        offer_details_result = get_offer_details(access_token, item_data['offer']['id'])
        
        line_item_defaults = {
            'order': order,
            'offer_id': item_data['offer']['id'],
            'offer_name': item_data['offer']['name'],
            'quantity': item_data['quantity'],
            'price': Decimal(item_data['price']['amount']),
            'bought_at': parse_datetime(item_data['boughtAt']),
        }
        
        if offer_details_result['success']:
            offer_data = offer_details_result['data']
            line_item_defaults.update({
                'image_url': offer_data['images'][0]['url'] if offer_data.get('images') else None,
                'external_id': offer_data.get('external', {}).get('id'),
                'offer_format': offer_data.get('sellingMode', {}).get('format'),
                'auction_end_time': parse_datetime(offer_data.get('publication', {}).get('endingAt')) if offer_data.get('publication', {}).get('endingAt') else None,
            })

        LineItem.objects.update_or_create(
            line_item_id=item_data['id'],
            defaults=line_item_defaults
        )
        
    return order, created