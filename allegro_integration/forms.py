from django import forms

class OfferCreateForm(forms.Form):

    CREATION_METHOD_CHOICES = [
        ('FROM_SCRATCH', 'Wystaw nową ofertę od zera'),
        ('FROM_EAN', 'Wyszukaj produkt po kodzie EAN i wystaw ofertę'),
        ('FROM_EXISTING', 'Sklonuj moją istniejącą ofertę'),
    ]
    creation_method = forms.ChoiceField(
        choices=CREATION_METHOD_CHOICES,
        label="Jak chcesz utworzyć ofertę?",
        widget=forms.RadioSelect,
        initial='FROM_SCRATCH'
    )
    
    ean_code = forms.CharField(
        label="Kod EAN produktu", 
        max_length=13, 
        required=False,
        help_text="Wypełnij, jeśli wybrałeś metodę 'Wyszukaj po kodzie EAN'."
    )
    
    existing_offer_id = forms.CharField(
        label="ID istniejącej oferty do sklonowania",
        required=False,
        help_text="Wypełnij, jeśli wybrałeś metodę 'Sklonuj ofertę'."
    )

    title = forms.CharField(
        label="Tytuł oferty", 
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'np. Smartfon XYZ 128GB Czarny'})
    )

    category_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    category_path_display = forms.CharField(
        label="Wybrana kategoria",
        required=False,
        disabled=True,
        help_text="Kategoria zostanie uzupełniona automatycznie po jej wybraniu w wyszukiwarce."
    )

    description_html = forms.CharField(
        label="Opis oferty (HTML)",
        widget=forms.Textarea(attrs={'rows': 15}),
        help_text="Możesz używać tagów HTML. Zalecane jest użycie edytora WYSIWYG."
    )
    
    images_urls = forms.CharField(
        label="Adresy URL zdjęć (jeden na linię)",
        widget=forms.Textarea(attrs={'rows': 5}),
        help_text="Wklej publicznie dostępne adresy URL do zdjęć. Pierwsze zdjęcie będzie miniaturką."
    )

    SELLING_MODE_CHOICES = [
        ('BUY_NOW', 'Kup Teraz'),
        ('AUCTION', 'Licytacja'),
    ]
    selling_mode = forms.ChoiceField(
        choices=SELLING_MODE_CHOICES,
        label="Format sprzedaży",
        widget=forms.RadioSelect,
        initial='BUY_NOW'
    )
    
    price_buy_now = forms.DecimalField(
        label="Cena 'Kup Teraz'", 
        max_digits=10, 
        decimal_places=2,
        required=False
    )
    
    price_auction_start = forms.DecimalField(
        label="Cena wywoławcza licytacji",
        max_digits=10,
        decimal_places=2,
        required=False
    )
    
    stock = forms.IntegerField(
        label="Liczba sztuk", 
        min_value=1,
        initial=1
    )

    DURATION_CHOICES = [
        ('P3D', '3 dni'),
        ('P5D', '5 dni'),
        ('P7D', '7 dni'),
        ('P10D', '10 dni'),
        ('P20D', '20 dni'),
        ('P30D', '30 dni'),
    ]
    publication_duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Czas trwania oferty",
        initial='P10D'
    )

    shipping_rates_id = forms.ChoiceField(
        label="Cennik dostaw",
        help_text="Cenniki muszą być wcześniej zdefiniowane na Twoim koncie Allegro."

    )

    dynamic_parameters = forms.CharField(widget=forms.HiddenInput(), required=False)


    def __init__(self, *args, **kwargs):
        shipping_rates_choices = kwargs.pop('shipping_rates_choices', [])
        super().__init__(*args, **kwargs)
        if shipping_rates_choices:
            self.fields['shipping_rates_id'].choices = shipping_rates_choices


    def clean(self):

        cleaned_data = super().clean()
        
        creation_method = cleaned_data.get('creation_method')
        selling_mode = cleaned_data.get('selling_mode')
        price_buy_now = cleaned_data.get('price_buy_now')
        price_auction_start = cleaned_data.get('price_auction_start')

        if creation_method == 'FROM_EAN' and not cleaned_data.get('ean_code'):
            self.add_error('ean_code', 'Kod EAN jest wymagany dla tej metody tworzenia.')
            
        if creation_method == 'FROM_EXISTING' and not cleaned_data.get('existing_offer_id'):
            self.add_error('existing_offer_id', 'ID istniejącej oferty jest wymagane dla tej metody.')

        if selling_mode == 'BUY_NOW':
            if not price_buy_now:
                self.add_error('price_buy_now', 'Cena "Kup Teraz" jest wymagana dla tego formatu sprzedaży.')
            if price_auction_start:
                self.add_error('price_auction_start', 'Cena wywoławcza nie dotyczy formatu "Kup Teraz".')

        elif selling_mode == 'AUCTION':
            if not price_auction_start:
                self.add_error('price_auction_start', 'Cena wywoławcza jest wymagana dla licytacji.')
            if price_buy_now:
                self.add_error('price_buy_now', 'Cena "Kup Teraz" nie dotyczy licytacji.')

        if not cleaned_data.get('category_id'):
            self.add_error('category_path_display', "Musisz wybrać kategorię dla oferty.")

        return cleaned_data

    def structure_payload(self):
        if not self.is_valid():
            raise ValueError("Formularz zawiera błędy i nie można utworzyć payloadu.")

        data = self.cleaned_data

        if data['selling_mode'] == 'BUY_NOW':
            selling_mode_payload = {
                "format": "BUY_NOW",
                "price": {
                    "amount": f"{data['price_buy_now']:.2f}",
                    "currency": "PLN"
                }
            }
        else:
            selling_mode_payload = {
                "format": "AUCTION",
                "startingPrice": {
                    "amount": f"{data['price_auction_start']:.2f}",
                    "currency": "PLN"
                }
            }

        description_payload = {
            "sections": [{
                "items": [{
                    "type": "TEXT",
                    "content": data['description_html']
                }]
            }]
        }

        image_urls = [url.strip() for url in data['images_urls'].splitlines() if url.strip()]

        payload = {
            "name": data['title'],
            "category": {"id": data['category_id']},
            "sellingMode": selling_mode_payload,
            "stock": {"available": data['stock'], "unit": "UNIT"},
            "publication": {"duration": data['publication_duration']},
            "delivery": {"shippingRates": {"id": data['shipping_rates_id']}},
            "description": description_payload,
            "images": [{"url": url} for url in image_urls],
            "parameters": [],
        }
        
        return payload