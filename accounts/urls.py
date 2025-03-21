from django.urls import path
from .views import (
    UserBaseViewSet, RefreshViewSet
)

urlpatterns = [
    path('token/', UserBaseViewSet.as_view({'post': 'login'})),
    path('refresh/', RefreshViewSet.as_view({'post': 'post'}), name='token_refresh'),
]