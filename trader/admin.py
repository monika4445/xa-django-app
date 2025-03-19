from django.contrib import admin
from .models import Trader, PercentSettings, CredsTrader, TraderPhone, BasePercentSettings, BaseRateSettings

@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'telegram_id', 
        'user_account', 
        'referal_id', 
        'email', 
        'ava_balance', 
        'block_balance', 
        'wallet', 
        'day_limit', 
        'admin_status', 
        'deposit_status', 
        'withdraw_status', 
        'reward', 
        'created_at', 
        'updated_at',
    )
    list_filter = ('admin_status', 'deposit_status', 'withdraw_status', 'created_at', 'updated_at')
    search_fields = ('id', 'telegram_id', 'email', 'user_account__username')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(PercentSettings)
class PercentSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'user_id', 
        'merchant_id', 
        'provider_id', 
        'deposit_percent', 
        'withdraw_percent', 
        'country', 
        'currency', 
        'method', 
        'created_at', 
        'updated_at',
    )
    list_filter = ('country', 'currency', 'created_at', 'updated_at')
    search_fields = ('id', 'user_id__telegram_id', 'merchant_id', 'provider_id')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(CredsTrader)
class CredsTraderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'user_id', 
        'phone_id', 
        'card_number', 
        'method', 
        'bank', 
        'holder', 
        'status', 
        'max_op', 
        'country', 
        'currency', 
        'created_at', 
        'updated_at',
    )
    list_filter = ('status', 'country', 'currency', 'created_at', 'updated_at')
    search_fields = ('id', 'user_id__telegram_id', 'card_number', 'bank')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(TraderPhone)
class TraderPhoneAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'user_id', 
        'name', 
        'status', 
        'is_online', 
        'created_at', 
        'updated_at',
    )
    list_filter = ('status', 'is_online', 'created_at', 'updated_at')
    search_fields = ('id', 'user_id__telegram_id', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')


admin.site.register(BasePercentSettings)
admin.site.register(BaseRateSettings)