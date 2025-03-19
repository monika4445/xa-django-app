from rest_framework.serializers import ModelSerializer, Serializer, CharField, IntegerField, SerializerMethodField, FloatField, BooleanField

from .models import (
    Appeal, SupportUser, Document
)


class RegisterSupportUserSerializer(Serializer):
    email = CharField()
    password = CharField()


class SupportUserSerialzier(ModelSerializer):
    class Meta:
        model = SupportUser
        fields = ['id', 'user_account', 'email', 'rating', 'reward', 'created_at', 'updated_at']


class DocumentSerialzier(ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'created_at', 'updated_at']


class DocumentCreateSerialzier(ModelSerializer):
    class Meta:
        model = Document
        fields = ['file']


class AppealSerializer(ModelSerializer):
    documents = SerializerMethodField()
    class Meta:
        model = Appeal
        fields = ['id', 'order_id', 'invoice_id', 'amount', 'sup_id',
                  'provider_id', 'responsible_id', 'status', 'source_id',
                  'documents', 'created_at', 'updated_at']

    def get_documents(self, obj):
        documents_obj = [Document.objects.get(id=document_id)
                         for document_id in obj.documents]

        serializer = [DocumentSerialzier(document_obj).data 
                      for document_obj in documents_obj]
        return serializer


class AppealCreateSerialzier(Serializer):
    order_id = CharField() # Либо order_id либо deal.id
    amount = CharField()
    documents = CharField()


class AppealAddDocumentSerialzier(Serializer):
    document_id = CharField()