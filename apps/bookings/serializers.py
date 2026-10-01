from rest_framework import serializers

from apps.bookings.models import Booking


class _NamedRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class _UserRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class BookingSerializer(serializers.ModelSerializer):
    user = _UserRefSerializer(read_only=True)
    service = _NamedRefSerializer(read_only=True)
    employee = _NamedRefSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'service', 'employee', 'start_at', 'end_at',
            'price', 'status', 'status_display', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class BookingCreateSerializer(serializers.Serializer):
    """Input format only; business rules live in bookings.services.create_booking."""

    service_id = serializers.IntegerField(min_value=1)
    employee_id = serializers.IntegerField(min_value=1)
    start_at = serializers.DateTimeField()


class BookingHistoryQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Booking.Status.choices, required=False)
    when = serializers.ChoiceField(choices=['upcoming', 'past'], required=False)


class SlotQuerySerializer(serializers.Serializer):
    service_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField(help_text='Local date in the business timezone, YYYY-MM-DD.')
    employee_id = serializers.IntegerField(min_value=1, required=False)


class SlotSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
