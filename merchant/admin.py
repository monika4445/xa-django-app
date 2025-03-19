from django import forms
from django.contrib import admin
from accounts.models import UserAccounts
from .models import Merchant, Deal, Client, SubMerchantAccount

class MerchantForm(forms.ModelForm):
    # Добавляем дополнительные поля для создания пользователя
    user_username = forms.CharField(
        label="Username",
        required=False,
        help_text="Введите имя пользователя для создания нового UserAccounts."
    )
    user_password = forms.CharField(
        label="Password",
        required=False,
        widget=forms.PasswordInput,
        help_text="Введите пароль для создания нового UserAccounts."
    )

    class Meta:
        model = Merchant
        fields = '__all__'

    def save(self, commit=True):
        """
        Сохраняем Merchant и создаем UserAccounts при необходимости.
        """
        instance = super().save(commit=False)

        username = self.cleaned_data.get("user_username")
        password = self.cleaned_data.get("user_password")

        if username and password and not instance.user_account:
            user_account = UserAccounts.objects.create_user(
                login=username,
                password=password
            )
            user_account.is_active = True
            user_account.is_confirmed = True
            user_account.in_consideration = True
            user_account.save()
            instance.user_account = user_account

        if commit:
            instance.save()

        return instance


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    form = MerchantForm
    list_display = (
        'id', 
        'user_account', 
        'group_id', 
        'referal_id', 
        'title', 
        'balance', 
        'status', 
        'total_settl', 
        'sla_on_trade', 
        'sla_on_appeals', 
        'max_amount_sla', 
        'created_at', 
        'updated_at',
    )
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('id', 'title', 'user_account__username', 'hash_api_key')
    readonly_fields = ('id', 'hash_api_key', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': (
                'id', 
                'user_account', 
                'user_username',  
                'user_password', 
                'group_id', 
                'referal_id', 
                'title', 
                'balance', 
                'hash_api_key', 
                'status', 
            )
        }),
        ('SLA Настройки', {
            'fields': (
                'sla_on_trade', 
                'sla_on_appeals', 
                'max_amount_sla',
            )
        }),
        ('Информация о времени', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def save_model(self, request, obj, form, change):
        """
        Дополнительная логика перед сохранением сущности, если нужно.
        """
        super().save_model(request, obj, form, change)



@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order_id', 
        'provider_invoice_id', 
        'provider_id', 
        'responsible_id', 
        'creds_id', 
        'amount', 
        'amount_by_currency',
        'amount_by_currency_merchant',
        'amount_by_currency_trader',
        'amount_by_currency_provider',
        'method', 
        'county', 
        'currency', 
        'webhook', 
        'status', 
        'type', 
        'rate', 
        'source_id', 
        'client_id', 
        'completed_at', 
        'created_at', 
        'updated_at',
    )
    list_filter = ('status', 'type', 'county', 'currency', 'created_at', 'updated_at')
    search_fields = ('id', 'order_id', 'provider_invoice_id', 'responsible_id__telegram_id', 'creds_id__card_number', 'client_id__id')
    readonly_fields = ('id', 'created_at', 'updated_at')


admin.site.register(Client)
admin.site.register(SubMerchantAccount)