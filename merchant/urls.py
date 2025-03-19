from django.urls import path
from .views import (
    UserBaseViewSet, MerchantDepositViewSet, MerchantWithdrawViewSet, SubMerchantAccountViewSet,
    ThreadDealsViewSet, EcomDealViewSet, EcomInternalComfirmViewSet, CreateOrderViewH2H, Send3DSCodeViewSet
)

urlpatterns = [
    path('me/', UserBaseViewSet.as_view({'get': 'me'})),

    path('deposit/', MerchantDepositViewSet.as_view({'post': 'create'})),
    path('withdraw/', MerchantWithdrawViewSet.as_view({'post': 'create'})),

    path('sub_account/', SubMerchantAccountViewSet.as_view({'post': 'create', 'get': 'sub_account_me'})),

    path('deals/thread/', ThreadDealsViewSet.as_view({'get': 'traffic'})),

    path('ecom/', EcomDealViewSet.as_view({'post': 'create'})),
    path('ecom/deposit/', EcomDealViewSet.as_view({'post': 'create'})),
    path('h2h/ecom/deposit/', CreateOrderViewH2H.as_view({'post': 'create'})),
    path('h2h/ecom/3ds/', Send3DSCodeViewSet.as_view({'post': 'create'})),
    path('ecom/internal/confirm', EcomInternalComfirmViewSet.as_view({'post': 'internal_confirm'})),
]