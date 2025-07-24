from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from .models import AllegroProfile, Client, Order, LineItem
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class AllegroProfileInline(admin.StackedInline):
    model = AllegroProfile
    can_delete = False
    verbose_name_plural = 'Profile Allegro'

    fields = ('access_token', 'refresh_token', 'token_expires_at', 'initiate_auth_button', 'refresh_token_button')

    readonly_fields = ('token_expires_at', 'initiate_auth_button', 'refresh_token_button')

    def initiate_auth_button(self, obj):
        if hasattr(obj, 'user'):
            url = reverse('allegro_integration:initiate_allegro_auth', args=[obj.user.pk])
            return format_html('<a class="button" href="{}">Połącz / Odnów połączenie z Allegro</a>', url)
        return "Zapisz użytkownika, aby wygenerować link."
    initiate_auth_button.short_description = "Zarządzanie połączeniem"

    def refresh_token_button(self, obj):
        if obj.pk and obj.refresh_token and hasattr(obj, 'user'):
            url = reverse('allegro_integration:refresh_allegro_token', args=[obj.user.pk])
            return format_html('<a class="button" href="{}">Odśwież Token (szybko)</a>', url)
        return "Brak tokenu odświeżającego do użycia."

    refresh_token_button.short_description = "Akcja odświeżania"

class CustomUserAdmin(BaseUserAdmin):
    inlines = (AllegroProfileInline,)

    def get_list_display(self, request):

        return super().get_list_display(request) + ('fetch_orders_button',)

    def fetch_orders_button(self, obj):
        if hasattr(obj, 'allegro_profile') and obj.allegro_profile.access_token:
            url = reverse('allegro_integration:process_allegro_orders', args=[obj.pk])
            return format_html('<a class="button" href="{}">Pobierz zamówienia</a>', url)
        return "Brak tokenu"
    fetch_orders_button.short_description = "Akcje Allegro"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('login', 'first_name', 'last_name', 'email', 'phone_number')
    search_fields = ('login', 'email', 'first_name', 'last_name', 'allegro_id')


class LineItemInline(admin.TabularInline):
    model = LineItem
    extra = 0 
    
    readonly_fields = ('display_image', 'offer_link', 'external_id', 'quantity', 'price', 'offer_format_display', 'end_time_display')
    fields = ('display_image', 'offer_link', 'external_id', 'quantity', 'price', 'offer_format_display', 'end_time_display')

    can_delete = False
    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False

    def offer_link(self, obj):
        url = f"https://allegro.pl.allegrosandbox.pl/oferta/{obj.offer_id}"
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.offer_name)
    offer_link.short_description = "Oferta"

    def offer_format_display(self, obj):
        return obj.get_offer_format_display() 
    offer_format_display.short_description = "Format"
    
    def end_time_display(self, obj):
        if obj.offer_format == 'AUCTION' and obj.auction_end_time:
            return obj.auction_end_time.strftime('%Y-%m-%d %H:%M:%S')
        return "—"
    end_time_display.short_description = "Koniec Licytacji"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('checkout_form_id', 'buyer_link', 'status', 'total_to_pay', 'allegro_updated_at')
    list_filter = ('status', 'user')
    search_fields = ('checkout_form_id', 'buyer__login', 'buyer__email')
    readonly_fields = ('created_at', 'modified_at')

    inlines = [LineItemInline]

    def buyer_link(self, obj):

        url = (
            reverse("admin:allegro_integration_order_changelist")
            + "?"
            + urlencode({"buyer__id__exact": f"{obj.buyer.id}"})
        )
        return format_html('<a href="{}">{}</a>', url, obj.buyer.login)
    buyer_link.short_description = "Kupujący"