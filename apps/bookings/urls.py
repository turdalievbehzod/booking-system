from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.bookings.views import AvailableSlotsView, BookingViewSet

router = DefaultRouter()
router.register('bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('slots/', AvailableSlotsView.as_view(), name='available-slots'),
    *router.urls,
]
