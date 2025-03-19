from django.urls import path, include
from accounts.urls import urlpatterns as accounts_app_urls
from merchant.urls import urlpatterns as merchant_app_urls
from trader.urls import urlpatterns as trader_app_urls
from support.urls import urlpatterns as support_app_urls

urlpatterns = [
    path('auth/', include(accounts_app_urls)),
    path('merchant/', include(merchant_app_urls)),
    path('trader/', include(trader_app_urls)),
    path('support/', include(support_app_urls)),
]