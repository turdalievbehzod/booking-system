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
