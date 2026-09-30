from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.bookings.selectors import get_available_slots, get_booking_history
from apps.bookings.serializers import (
    BookingCreateSerializer,
    BookingHistoryQuerySerializer,
    BookingSerializer,
    SlotQuerySerializer,
    SlotSerializer,
)
from apps.bookings.services import change_status, create_booking
from apps.users.permissions import IsBusinessAdmin


class AvailableSlotsView(APIView):
    """Free time slots for a service on a given date. Public, so visitors can browse before logging in."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(parameters=[SlotQuerySerializer], responses=SlotSerializer(many=True))
    def get(self, request):
        query = SlotQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        slots = get_available_slots(
            service_id=query.validated_data['service_id'],
            date=query.validated_data['date'],
            employee_id=query.validated_data.get('employee_id'),
        )
        return Response(SlotSerializer(slots, many=True).data)


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    list     - booking history (own bookings; admin sees all). Filters: ?status=, ?when=upcoming|past
    create   - book a slot (starts as pending)
    cancel   - customer (own, before deadline) or admin
    confirm / complete - admin only
    """

    serializer_class = BookingSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # schema generation, no real user
            return Booking.objects.none()
        query = BookingHistoryQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        return get_booking_history(self.request.user, **query.validated_data)

    @extend_schema(parameters=[BookingHistoryQuerySerializer])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=BookingCreateSerializer, responses={201: BookingSerializer})
    def create(self, request, *args, **kwargs):
        data = BookingCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        booking = create_booking(user=request.user, **data.validated_data)
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    def _change_status(self, pk, new_status):
        booking = change_status(booking_id=pk, new_status=new_status, actor=self.request.user)
        return Response(BookingSerializer(booking).data)

    @extend_schema(request=None, responses=BookingSerializer)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        return self._change_status(pk, Booking.Status.CANCELLED)

    @extend_schema(request=None, responses=BookingSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsBusinessAdmin])
    def confirm(self, request, pk=None):
        return self._change_status(pk, Booking.Status.CONFIRMED)

    @extend_schema(request=None, responses=BookingSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsBusinessAdmin])
    def complete(self, request, pk=None):
        return self._change_status(pk, Booking.Status.COMPLETED)
