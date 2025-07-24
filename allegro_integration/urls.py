from django.urls import path
from . import views

app_name = 'allegro_integration'

urlpatterns = [
    path(
        'fetch-orders/<int:user_id>/', 
        views.fetch_allegro_orders_view, 
        name='fetch_allegro_orders'
    ),
    path(
        'refresh-token/<int:user_id>/', 
        views.refresh_allegro_token_view, 
        name='refresh_allegro_token'
    ),
    path(
        'initiate-auth/<int:user_id>/', 
        views.initiate_allegro_auth_view, 
        name='initiate_allegro_auth'
    ),
    path(
        'oauth/callback/', 
        views.allegro_oauth_callback_view, 
        name='allegro_oauth_callback'
    ),
    path(
        'process-orders/<int:user_id>/', 
        views.process_allegro_orders_view, 
        name='process_allegro_orders'
    ),

    path('offer/create/', views.create_offer_view, name='create_offer'),

    path('api/search-category/', views.search_category_api_view, name='api_search_category'),
    path('api/category-parameters/<str:category_id>/', views.get_category_parameters_api_view, name='api_get_category_parameters'),
]