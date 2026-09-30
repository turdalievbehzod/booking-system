from django.contrib import admin, messages

from apps.bookings.models import Booking
from apps.bookings.services import change_status


def _bulk_change_status(modeladmin, request, queryset, new_status):
    # Goes through the same business rules as the API (allowed transitions, emails).
    changed = 0
    for booking in queryset:
        try:
            change_status(booking.pk, new_status, request.user)
            changed += 1
        except Exception as exc:
            modeladmin.message_user(request, f'#{booking.pk}: {exc}', messages.WARNING)
    modeladmin.message_user(request, f'{changed} booking(s) set to {new_status}.')


@admin.action(description='Confirm selected bookings')
def confirm_bookings(modeladmin, request, queryset):
    _bulk_change_status(modeladmin, request, queryset, Booking.Status.CONFIRMED)


@admin.action(description='Cancel selected bookings')
def cancel_bookings(modeladmin, request, queryset):
    _bulk_change_status(modeladmin, request, queryset, Booking.Status.CANCELLED)


@admin.action(description='Complete selected bookings')
def complete_bookings(modeladmin, request, queryset):
    _bulk_change_status(modeladmin, request, queryset, Booking.Status.COMPLETED)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'employee', 'start_at', 'end_at', 'price', 'status']
    list_filter = ['status', 'employee', 'service']
    search_fields = ['user__username', 'user__email', 'employee__name', 'service__name']
    date_hierarchy = 'start_at'
    list_select_related = ['user', 'service', 'employee']
    actions = [confirm_bookings, cancel_bookings, complete_bookings]
    # Bookings are created through the API so all validation applies;
    # in the admin only the status changes, via the actions above.
    readonly_fields = [f.name for f in Booking._meta.fields]

    def has_add_permission(self, request):
        return False
