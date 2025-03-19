from rest_framework.serializers import ModelSerializer, Serializer, CharField, IntegerField, SerializerMethodField, FloatField, BooleanField

from .models import (
    Trader, PercentSettings, TraderPhone, CredsTrader
)


class UserTraderSerialzier(ModelSerializer):
    percents = SerializerMethodField()
    class Meta:
        model = Trader
        fields = ['id', 'user_account', 'email', 'telegram_id', 
                  'ava_balance', 'block_balance', 'deposit_status', 'withdraw_status',
                  'reward', 'percents']
        
    def get_percents(self, obj):
        percent_settings_objs = PercentSettings.objects.filter(user_id=obj.id)
        
        percents = [dict(deposit_percent=percent_settings.deposit_percent,
                withdraw_percent=percent_settings.withdraw_percent,
                country=percent_settings.country,
                currency=percent_settings.currency) for percent_settings in percent_settings_objs]
        return percents


class RegisterTraderSeialzier(Serializer):
    email = CharField()
    password = CharField()
    available_deposit = FloatField()
    blocked_deposit = FloatField()
    deposit_percent = FloatField()
    withdraw_percent = FloatField()



class TraderPhoneSerialzier(ModelSerializer):
    class Meta:
        model = TraderPhone
        fields = ['id', 'name', 'user_id', 'status', 'is_online', 'created_at', 'updated_at']
    

class TraderPhoneCreateSerializer(Serializer):
    name = CharField()


class TraderCreadsSerializer(ModelSerializer):
    class Meta:
        model = CredsTrader
        fields = ['id', 'phone_id', 'user_id', 'method', 'card_number',
                  'status', 'holder', 'bank', 'max_op', 'country', 'currency']


class TraderCreadsCreateSerializer(Serializer):
    phone_id = CharField()
    card_number = CharField()
    method = CharField()
    max_op = CharField()
    holder = CharField()
    status = BooleanField()
    bank = CharField()
    country = CharField()
    currency = CharField()


class NotificationUrlTelegramTraderSerialzier(Serializer):
    tg_bot_url = CharField()


class NotificationDataTelegramTraderSerialzier(Serializer):
    trader_id = CharField()
    telegram_id = CharField()