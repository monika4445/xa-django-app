from django.urls import path
from .views import (
    UserBaseViewSet, TraderPhoneViewSet, TraderCreadsViewSet, TraderRequestViewSet,
    TraderOrderViewSet, NotificationTraderTelegramViewSet
)

urlpatterns = [
    path('register/', UserBaseViewSet.as_view({'post': 'create'})),
    path('me/', UserBaseViewSet.as_view({'get': 'me'})),

    path('phones/', TraderPhoneViewSet.as_view({'post': 'create', 'get': 'lists'})),
    path('phones/<str:phone_id>/', TraderPhoneViewSet.as_view({'delete': 'delete'})),

    path('credentials/', TraderCreadsViewSet.as_view({'post': 'create', 'get': 'lists'})),
    path('credentials/<str:cred_id>/', TraderCreadsViewSet.as_view({'put': 'update'})),
    path('credentials/<str:cred_id>/toggle/', TraderCreadsViewSet.as_view({'patch': 'toggle'})),

    path('requests/', TraderRequestViewSet.as_view({'get': 'trader_request_list'})),
    path('requests/<str:order_id>/toggle/', TraderRequestViewSet.as_view({'get': 'toggle_trader_request'})),

    path('orders/', TraderOrderViewSet.as_view({'get': 'trader_order_list'})),
    path('orders/active/', TraderOrderViewSet.as_view({'get': 'list_active_order_trader'})),
    path('orders/<str:order_id>/toggle/', TraderOrderViewSet.as_view({'patch': 'toggle_active_order'})),
    path('orders/<str:order_id>/<str:creds_id>/take/work/', TraderOrderViewSet.as_view({'post': 'take_order_to_work'})),

    path('notification/', NotificationTraderTelegramViewSet.as_view({'get': 'get_tg_bot_url', 'post': 'append_telegram_id_to_trader'})),
]