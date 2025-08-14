from django.urls import path, include
from rest_framework import routers
from listings import views
from listings.views import InitiatePaymentAPIView, VerifyPaymentAPIView, ChapaWebhookAPIView

router = routers.DefaultRouter()
router.register(r'bookings', views.BookingViewSet, basename='bookings')
router.register(r'property', views.ListingViewSet, basename='property')
router.register(r'user', views.UserViewset, basename='user')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),  # <-- COMMA ADDED
    path('api/payments/initiate/', InitiatePaymentAPIView.as_view(), name='payments-initiate'),
    path('api/payments/verify/', VerifyPaymentAPIView.as_view(), name='payments-verify'),
    path('api/payments/webhook/', ChapaWebhookAPIView.as_view(), name='payments-webhook'),
]
