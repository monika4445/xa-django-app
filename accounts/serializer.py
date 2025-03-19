from rest_framework.serializers import ModelSerializer, Serializer, CharField, IntegerField, SerializerMethodField, FloatField, BooleanField


class RefreshTokenSerialzierPost(Serializer):
    refresh = CharField()


class LoginSerializer(Serializer):
    username = CharField()
    password = CharField()


class LoginResponceSerialzier(Serializer):
    access = CharField()
    refresh = CharField()
    in_moderation = BooleanField()
    id_user = CharField()