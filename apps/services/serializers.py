from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.services.models import Availability, Employee, Service


class EmployeeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name']


class ServiceSerializer(serializers.ModelSerializer):
    employees = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'duration_minutes', 'price',
            'is_active', 'employees', 'created_at',
        ]
        read_only_fields = ['created_at']

    @extend_schema_field(EmployeeShortSerializer(many=True))
    def get_employees(self, obj):
        # Customers only need to see employees they can actually book.
        employees = [e for e in obj.employees.all() if e.is_active]
        return EmployeeShortSerializer(employees, many=True).data


class EmployeePublicSerializer(serializers.ModelSerializer):
    """What customers see: no email, no inactive flag."""

    service_ids = serializers.PrimaryKeyRelatedField(source='services', many=True, read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'service_ids']


class EmployeeAdminSerializer(serializers.ModelSerializer):
    service_ids = serializers.PrimaryKeyRelatedField(
        source='services',
        many=True,
        queryset=Service.objects.all(),
        required=False,
    )

    class Meta:
        model = Employee
        fields = ['id', 'name', 'email', 'is_active', 'service_ids', 'created_at']
        read_only_fields = ['created_at']

    def validate_email(self, value):
        return value.lower()

    def create(self, validated_data):
        services = validated_data.pop('services', [])
        employee = Employee.objects.create(**validated_data)
        employee.services.set(services)
        return employee

    def update(self, instance, validated_data):
        services = validated_data.pop('services', None)
        instance = super().update(instance, validated_data)
        if services is not None:
            instance.services.set(services)
        return instance


class AvailabilitySerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Availability
        fields = ['id', 'employee', 'day_of_week', 'day_of_week_display', 'start_time', 'end_time', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, attrs):
        # DRF does not call Model.clean(), so run the model's own validation
        # (start < end, no overlap with the employee's other hours that day).
        instance = Availability(**{**self._current_values(), **attrs})
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return attrs

    def _current_values(self):
        if self.instance is None:
            return {}
        return {
            'pk': self.instance.pk,
            'employee': self.instance.employee,
            'day_of_week': self.instance.day_of_week,
            'start_time': self.instance.start_time,
            'end_time': self.instance.end_time,
        }
