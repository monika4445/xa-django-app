from django.contrib.auth.models import update_last_login

from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from utils import BaseCRUD, CustomPagination
from .models import (
    UserAccounts
)
from .serializer import (
    RefreshTokenSerialzierPost, LoginResponceSerialzier, LoginSerializer
)


class UserBaseViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = LoginResponceSerialzier
    pagination_class = CustomPagination

    _model = UserAccounts
    _serializer = serializer_class

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: LoginResponceSerialzier, 400: 'Bad Request'},
        operation_summary="Login All User Account",
        operation_description="This endpoint login All user account.",
        tags=["JWT"]
    )
    def login(self, request):
        serialzier = LoginSerializer(data=request.data)
        if serialzier.is_valid():
            try:
                user = UserAccounts.objects.get(login=serialzier.data['username'])
            except:
                return Response({"message": 'This user not found in system'}, 400)

            if not user.check_password(serialzier.data['password']):
                return Response({"message": "Invalid password"}, status=400)

            refresh = RefreshToken.for_user(user)
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'in_moderation': user.in_consideration,
                'id_user': user.id,
            }
            update_last_login(None, user)
            return Response(data, 200)
        else:
            return Response(serialzier.errors, 400)

        

class RefreshViewSet(GenericViewSet):
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(
        request_body=RefreshTokenSerialzierPost,
        responses={200: TokenRefreshSerializer, 400: 'Bad Request'},
        operation_summary="Refresh JWT Token",
        operation_description="This endpoint refresh JWT token.",
        tags=["JWT"]
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        if serializer.is_valid():
            return Response(serializer.validated_data, 200)
        else:
            return Response(serializer.errors, 400)
