from django.urls import path

from .views import (
    DocumentViewSet, UserBaseViewSet, AppealViewSet
)

urlpatterns = [
    path('register/', UserBaseViewSet.as_view({'post': 'create'})),
    path('me/', UserBaseViewSet.as_view({'get': 'me'})),

    path('document/', DocumentViewSet.as_view({'post': 'create'})),

    path('appeal/', AppealViewSet.as_view({'post': 'create', 'get': 'list'})),
    path('appeal/<str:appeal_id>/', AppealViewSet.as_view({'put': 'update_document_appeal_by_trader'})),

    path('appeal/trader/<str:appeal_id>/', AppealViewSet.as_view({'post': 'toggle_appeal_to_trader'})),
    path('appeal/merchant/<str:appeal_id>/', AppealViewSet.as_view({'post': 'toggle_appeal_to_merchant'})),
]