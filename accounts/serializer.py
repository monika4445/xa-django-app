from packaging.utils import _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BooleanField
from rest_framework.serializers import Serializer, CharField, ChoiceField, DateField, IntegerField

from accounts.models import UserAccounts
from utils.password_validation import validator


class RefreshTokenSerialzierPost(Serializer):
  refresh = CharField()


class LoginSerializer(Serializer):
  login = CharField()
  password = CharField()


class LoginResponceSerialzier(Serializer):
  access = CharField()
  refresh = CharField()
  in_moderation = BooleanField()
  id_user = IntegerField()


class RegistrationSerializer(Serializer):
  login = CharField(max_length=30)
  password = CharField(write_only=True)
  first_name = CharField(max_length=255, required=False, allow_blank=True)
  last_name = CharField(max_length=255, required=False, allow_blank=True)
  patronymic_name = CharField(max_length=255, required=False, allow_blank=True)
  avatar = CharField(max_length=255, required=False, allow_blank=True)
  birthday = DateField(required=False, allow_null=True)
  role = ChoiceField(choices=UserAccounts.Role.choices, default=UserAccounts.Role.MERCHANT)

  def validate_login(self, value):
    if UserAccounts.objects.filter(login=value).exists():
      raise ValidationError(_('This login is already in use.'))
    return value

  def validate_password(self, value):
    try:
        validator.validate(value)
    except ValidationError as e:
        raise ValidationError({'password': e.messages[0]})
    return value


  def create(self, validated_data):
    validated_data.setdefault('is_confirmed', False)
    validated_data.setdefault('in_consideration', True)
    return UserAccounts.objects.create_user(**validated_data)
