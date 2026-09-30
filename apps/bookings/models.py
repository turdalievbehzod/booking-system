from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Func, Q

from apps.services.models import Employee, Service


class TsTzRange(Func):
    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    # Only these statuses occupy a time slot.
    ACTIVE_STATUSES = [Status.PENDING, Status.CONFIRMED]

    # Allowed status transitions; anything else is rejected by the business logic.
    TRANSITIONS = {
        Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.COMPLETED, Status.CANCELLED},
        Status.CANCELLED: set(),
        Status.COMPLETED: set(),
    }

    # PROTECT: a user/employee/service that has bookings cannot be deleted
    # (deactivate it with is_active instead), so booking history is never lost.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bookings')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')

    # Stored in UTC (USE_TZ=True). end_at and price are snapshots taken at booking time,
    # so later changes to the service's duration or price don't rewrite old bookings.
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_at']
        constraints = [
            models.CheckConstraint(condition=Q(end_at__gt=F('start_at')), name='booking_end_after_start'),
            models.CheckConstraint(condition=Q(price__gte=0), name='booking_price_non_negative'),
            # Race-condition guard: PostgreSQL rejects a second active booking whose
            # [start_at, end_at) overlaps another for the same employee, even if two
            # requests pass the application-level check at the same moment.
            ExclusionConstraint(
                name='booking_no_overlap_per_employee',
                expressions=[
                    (TsTzRange('start_at', 'end_at', RangeBoundary()), RangeOperators.OVERLAPS),
                    ('employee', RangeOperators.EQUAL),
                ],
                condition=Q(status__in=['pending', 'confirmed']),
            ),
        ]
        indexes = [
            models.Index(fields=['employee', 'start_at']),
            models.Index(fields=['user', '-start_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'#{self.pk} {self.service} with {self.employee} at {self.start_at:%Y-%m-%d %H:%M}'

    def can_transition_to(self, new_status):
        return new_status in self.TRANSITIONS[self.status]
