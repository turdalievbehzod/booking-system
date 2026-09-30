from django.contrib import admin

from apps.services.models import Availability, Employee, EmployeeService, Service


class EmployeeServiceInline(admin.TabularInline):
    model = EmployeeService
    extra = 1


class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'price', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    inlines = [EmployeeServiceInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'email']
    inlines = [EmployeeServiceInline, AvailabilityInline]


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['employee', 'day_of_week', 'start_time', 'end_time']
    list_filter = ['day_of_week', 'employee']
