from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from listings import views

router =routers.DefaultRouter()
router.register(r'bookings', views.BookingViewSet, basename='bookings')
router.register(r'property', views.ListingViewSet, basename='property')
router.register(r'user', views.UserViewset, basename='User')

#["NestedDefaultRouter"]
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/',include('rest_framework.urls'))
]