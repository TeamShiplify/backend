from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html

class AllegroProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='allegro_profile')
    access_token = models.CharField(max_length=2048, blank=True, null=True, verbose_name="Token dostępowy Allegro")
    refresh_token = models.CharField(max_length=2048, blank=True, null=True, verbose_name="Token odświeżający Allegro")
    token_expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Token wygasa o")

    def __str__(self):
        return f"Profil Allegro dla {self.user.username}"

class Client(models.Model):
    allegro_id = models.CharField(max_length=255, unique=True, db_index=True, help_text="Unikalny ID użytkownika z Allegro")
    login = models.CharField(max_length=255, db_index=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.login})"
        
    class Meta:
        verbose_name = "Klient Allegro"
        verbose_name_plural = "Klienci Allegro"

class Order(models.Model):
    STATUS_CHOICES = [
        ('BOUGHT', 'Kupione'),
        ('FILLED_IN', 'Wypełniono formularz'),
        ('READY_FOR_PROCESSING', 'Gotowe do realizacji'),
    ]
    
    buyer = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='orders', help_text="Klient, który złożył zamówienie")
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Użytkownik systemowy (sprzedawca)")
    checkout_form_id = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    allegro_updated_at = models.DateTimeField()
    delivery_method_name = models.CharField(max_length=255)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_street = models.CharField(max_length=255)
    delivery_city = models.CharField(max_length=255)
    delivery_post_code = models.CharField(max_length=20)
    delivery_country_code = models.CharField(max_length=2)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    total_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Zamówienie {self.checkout_form_id}"

    class Meta:
        ordering = ['-allegro_updated_at']
        verbose_name = "Zamówienie Allegro"
        verbose_name_plural = "Zamówienia Allegro"

class LineItem(models.Model):
    FORMAT_CHOICES = [
        ('BUY_NOW', 'Kup Teraz'),
        ('AUCTION', 'Licytacja'),
        ('ADVERTISEMENT', 'Ogłoszenie'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='line_items')
    line_item_id = models.CharField(max_length=255, unique=True, db_index=True)
    offer_id = models.CharField(max_length=255, db_index=True)
    offer_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    bought_at = models.DateTimeField()
    image_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name="URL zdjęcia")
    external_id = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Sygnatura (SKU)")
    offer_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, blank=True, null=True, verbose_name="Format oferty")
    auction_end_time = models.DateTimeField(blank=True, null=True, verbose_name="Koniec licytacji")
    
    def __str__(self):
        return f"{self.offer_name} (x{self.quantity})"

    def display_image(self):
        if self.image_url:
            return format_html('<img src="{}" width="60" height="60" />', self.image_url)
        return "Brak zdjęcia"
    display_image.short_description = "Zdjęcie"

    class Meta:
        verbose_name = "Pozycja zamówienia"
        verbose_name_plural = "Pozycje zamówienia"