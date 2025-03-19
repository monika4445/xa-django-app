from rest_framework.serializers import (
    ModelSerializer, Serializer, SerializerMethodField,
    CharField, IntegerField, FloatField, BooleanField, EmailField,
    DecimalField, URLField, UUIDField, DateTimeField

)
from .models import (
    Merchant, Deal, Client, SubMerchantAccount
)
from trader.models import CredsTrader
from trader.serializer import TraderCreadsSerializer

class MerchantSerialzier(ModelSerializer):
    class Meta:
        model = Merchant
        fields = ['id', 'user_account', 'group_id', 'referal_id', 'title', 'balance',
                  'hash_api_key', 'status', 'total_settl', 'sla_on_trade', 'sla_on_appeals',
                  'max_amount_sla', 'created_at', 'updated_at']



class ClientSerializer(Serializer):
    id = CharField()
    first_name = CharField()
    last_name = CharField()
    phone_number = CharField()
    email = EmailField()


class RequisiteSerialzier(Serializer):
    number = CharField()
    holder_name = CharField()
    bank = CharField()


class MerchantRequestDepositSerialzier(Serializer):
    id = CharField()
    county = CharField()
    currency = CharField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    webhook = URLField()
    method = CharField()
    client = ClientSerializer(required=False)
    mRate = DecimalField(max_digits=10, decimal_places=2, required=False)


class MerchantResponseDepositSerialzier(Serializer):
    id = CharField()
    invoice_id = CharField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    amount_by_currency = DecimalField(max_digits=10, decimal_places=2)
    rate = DecimalField(max_digits=10, decimal_places=2)
    requisite = RequisiteSerialzier()



class MerchantWithdrawRequestSeraialzier(Serializer):
    id = CharField()
    county = CharField()
    currency = CharField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    webhook = URLField()
    method = CharField()
    client = ClientSerializer()
    requisite = RequisiteSerialzier()


class MerchantWithdrawResponseSerialzier(Serializer):
    id = CharField()
    invoice_id = CharField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    amount_by_currency = DecimalField(max_digits=10, decimal_places=2)
    rate = DecimalField(max_digits=10, decimal_places=2)



class DealSerialzier(ModelSerializer):
    creds_id = SerializerMethodField()

    class Meta:
        model = Deal
        fields = ['order_id', 'provider_id', 'responsible_id', 'creds_id', 'amount', 'amount_by_currency',
                  'method', 'county', 'currency', 'webhook', 'holder_name_rec', 'number_rec', 'bank',
                  'status', 'type', 'rate', 'decode_holder_name_client', 'decode_number_client',
                  'decode_bank_client', 'source_id', 'client_id', 'created_at', 'updated_at']

    def get_creds_id(self, obj):
        if obj.creds_id is None:
            return None
        creds_id = CredsTrader.objects.get(id=obj.creds_id.id)
        return TraderCreadsSerializer(creds_id).data



class EcomCreateDealSerializer(Serializer):
    id = CharField()
    amount = CharField()
    webhook = CharField()
    success_url = CharField()
    failed_url = CharField()

class Requisite(Serializer):
    number = CharField()
    ex_date = CharField()
    cvv = CharField()
    holder_name = CharField()

class ThreeDSCodeSerializer(Serializer):
    id = CharField()
    code = CharField()

class ThreeDSCodeResponseSerializer(Serializer):
    id = CharField()
    status = BooleanField()

class EcomCreateDealSerializerH2H(Serializer):
    id = CharField()
    amount = CharField()
    webhook = CharField()
    success_url = CharField()
    failed_url = CharField()
    requisite = Requisite()


class EcomResponseDealSerializer(Serializer):
    id = CharField()
    invoice_id = CharField()
    amount = CharField()
    amount_by_currency = CharField()
    rate = CharField()
    payment_link = CharField()


class SubMerchantAccountCreateSerialzier(Serializer):
    email = CharField()
    password = CharField()
    role = CharField()


class SubMerchantAccauntSerialzier(ModelSerializer):
    class Meta:
        model = SubMerchantAccount
        fields = ['id', 'merchant_user', 'user_account', 'role', 'created_at', 'updated_at']


class DealSerializer(Serializer):
    id = UUIDField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField()
    method = CharField()
    created_at = DateTimeField()
    status = CharField()


class PercentSettingsSerializer(Serializer):
    currency = CharField()
    deposit_percent = FloatField()
    withdraw_percent = FloatField()
    deals = DealSerializer(many=True)


class MerchantTrafficSerializer(Serializer):
    country = CharField()
    details = PercentSettingsSerializer(many=True)


class EcomInteranlConfirmSerialzier(Serializer):
    order_id = CharField()


class EcomInteranlConfirmResponseSerialzier(Serializer):
    message = CharField()