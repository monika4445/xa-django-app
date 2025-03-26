from django.urls import path
from .views import (
    UserBaseViewSet, RefreshViewSet, RegistrationView, LogoutView
)

urlpatterns = [
    path('token/', UserBaseViewSet.as_view({'post': 'login'})),
    path('refresh/', RefreshViewSet.as_view({'post': 'post'}), name='token_refresh'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout')
]

