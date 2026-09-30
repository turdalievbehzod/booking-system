from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.bookings.selectors import count_upcoming_bookings
from apps.services.models import Availability, Employee, Service
from apps.services.serializers import (
    AvailabilitySerializer,
    EmployeeAdminSerializer,
    EmployeePublicSerializer,
    ServiceSerializer,
)
from apps.users.permissions import IsBusinessAdminOrReadOnly, is_business_admin


class ServiceViewSet(viewsets.ModelViewSet):
    """
    Customers see active services only. Admin manages services.
    DELETE deactivates instead of deleting, because past bookings reference the service.
    """

    serializer_class = ServiceSerializer
    permission_classes = [IsBusinessAdminOrReadOnly]

    def get_queryset(self):
        qs = Service.objects.prefetch_related('employees')
        if not is_business_admin(self.request.user):
            qs = qs.filter(is_active=True)
        return qs

    def perform_destroy(self, instance):
        # Existing bookings stay valid; the service just can't be booked anymore.
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Customers see active employees (without email). Admin manages employees and
    which services each one provides (service_ids).
    """

    permission_classes = [IsBusinessAdminOrReadOnly]

    def get_queryset(self):
        qs = Employee.objects.prefetch_related(
            Prefetch('services', queryset=Service.objects.only('id')),
        )
        if not is_business_admin(self.request.user):
            qs = qs.filter(is_active=True)
        service_id = self.request.query_params.get('service_id')
        if service_id and service_id.isdigit():
            qs = qs.filter(services__id=service_id)
        return qs

    def get_serializer_class(self):
        if is_business_admin(self.request.user):
            return EmployeeAdminSerializer
        return EmployeePublicSerializer

    def update(self, request, *args, **kwargs):
        if request.data.get('is_active') in (False, 'false', 'False', 0, '0'):
            blocked = self._deactivation_blocked(self.get_object())
            if blocked:
                return blocked
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        employee = self.get_object()
        blocked = self._deactivation_blocked(employee)
        if blocked:
            return blocked
        employee.is_active = False
        employee.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _deactivation_blocked(employee):
        """An employee with upcoming bookings can't be deactivated silently:
        the admin must cancel or handle those bookings first."""
        upcoming = count_upcoming_bookings(employee)
        if upcoming:
            return Response(
                {'detail': f'Employee has {upcoming} upcoming booking(s). Cancel them first.'},
                status=status.HTTP_409_CONFLICT,
            )
        return None


class AvailabilityViewSet(viewsets.ModelViewSet):
    """Weekly working hours. Filter with ?employee=<id>."""

    serializer_class = AvailabilitySerializer
    permission_classes = [IsBusinessAdminOrReadOnly]

    def get_queryset(self):
        qs = Availability.objects.select_related('employee')
        if not is_business_admin(self.request.user):
            qs = qs.filter(employee__is_active=True)
        employee_id = self.request.query_params.get('employee')
        if employee_id and employee_id.isdigit():
            qs = qs.filter(employee_id=employee_id)
        return qs
