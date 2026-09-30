from rest_framework.routers import DefaultRouter

from apps.services.views import AvailabilityViewSet, EmployeeViewSet, ServiceViewSet

router = DefaultRouter()
router.register('services', ServiceViewSet, basename='service')
router.register('employees', EmployeeViewSet, basename='employee')
router.register('availabilities', AvailabilityViewSet, basename='availability')

urlpatterns = router.urls
