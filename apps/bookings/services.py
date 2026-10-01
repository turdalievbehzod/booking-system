"""
Booking write operations (HackSoft styleguide: services change state, selectors read).
Views stay thin and call these functions; admin, Celery tasks and tests use them too.
"""
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from apps.bookings.models import Booking
from apps.bookings.selectors import (
    BOOKING_HORIZON_DAYS,
    SLOT_STEP_MINUTES,
    business_tz,
    find_availability_window,
    is_admin,
)
from apps.services.models import Employee, EmployeeService, Service

logger = logging.getLogger(__name__)

CANCELLATION_DEADLINE_HOURS = getattr(settings, 'BOOKING_CANCELLATION_DEADLINE_HOURS', 2)

# PostgreSQL SQLSTATEs: exclusion_violation (our no-overlap constraint) and
# deadlock_detected. Concurrent inserts into the same slot can deadlock while
# checking the exclusion constraint; Postgres aborts one of them, which means
# that request lost the race for the slot.
EXCLUSION_VIOLATION = '23P01'
DEADLOCK_DETECTED = '40P01'


class SlotUnavailable(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This time slot is no longer available.'
    default_code = 'slot_unavailable'


def _sqlstate(exc):
    cause = exc.__cause__
    # psycopg2 exposes `pgcode`, psycopg3 exposes `sqlstate`.
    return getattr(cause, 'pgcode', None) or getattr(cause, 'sqlstate', None)


def _is_exclusion_violation(exc):
    return _sqlstate(exc) == EXCLUSION_VIOLATION


def _notify(booking, event):
    # Imported here to avoid a circular import (tasks -> services).
    from apps.bookings.tasks import send_booking_email

    def enqueue():
        try:
            send_booking_email.delay(booking.pk, event)
        except Exception:
            # A broken mail queue must not fail a booking that is already saved.
            logger.exception('Could not enqueue booking email (booking=%s, event=%s)', booking.pk, event)

    # Send only after the transaction commits: never email about a booking
    # that was rolled back.
    transaction.on_commit(enqueue)


def create_booking(user, service_id, employee_id, start_at):
    if timezone.is_naive(start_at):
        raise ValidationError({'start_at': 'Datetime must include a timezone offset.'})

    service = Service.objects.filter(pk=service_id, is_active=True).first()
    if service is None:
        raise ValidationError({'service_id': 'Service not found or inactive.'})

    employee = Employee.objects.filter(pk=employee_id, is_active=True).first()
    if employee is None:
        raise ValidationError({'employee_id': 'Employee not found or inactive.'})

    if not EmployeeService.objects.filter(employee=employee, service=service).exists():
        raise ValidationError({'employee_id': 'This employee does not provide this service.'})

    now = timezone.now()
    if start_at <= now:
        raise ValidationError({'start_at': 'Cannot book a time in the past.'})
    if start_at > now + timedelta(days=BOOKING_HORIZON_DAYS):
        raise ValidationError({'start_at': f'Bookings are allowed at most {BOOKING_HORIZON_DAYS} days ahead.'})

    end_at = start_at + timedelta(minutes=service.duration_minutes)

    window = find_availability_window(employee, start_at, end_at)
    if window is None:
        raise ValidationError({'start_at': 'The employee is not working at this time.'})

    # Only the start times offered by get_available_slots are accepted, so an API client
    # can't book 10:07 and leave unusable gaps in the schedule.
    local_start = timezone.localtime(start_at, business_tz())
    window_start = datetime.combine(local_start.date(), window.start_time, tzinfo=local_start.tzinfo)
    if (local_start - window_start) % timedelta(minutes=SLOT_STEP_MINUTES):
        raise ValidationError({'start_at': 'Please choose one of the offered time slots.'})

    # The same customer can't be in two places at once (different employees).
    if Booking.objects.filter(
        user=user,
        status__in=Booking.ACTIVE_STATUSES,
        start_at__lt=end_at,
        end_at__gt=start_at,
    ).exists():
        raise ValidationError({'start_at': 'You already have a booking that overlaps this time.'})

    # Fast path with a friendly error. It is NOT enough on its own: two concurrent
    # requests can both pass it. The DB exclusion constraint below is the real guard.
    if Booking.objects.filter(
        employee=employee,
        status__in=Booking.ACTIVE_STATUSES,
        start_at__lt=end_at,
        end_at__gt=start_at,
    ).exists():
        raise SlotUnavailable()

    try:
        # Savepoint, so a constraint failure doesn't break an outer transaction.
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                employee=employee,
                service=service,
                start_at=start_at,
                end_at=end_at,
                price=service.price,  # snapshot
                status=Booking.Status.PENDING,
            )
    except IntegrityError as exc:
        if _is_exclusion_violation(exc):
            raise SlotUnavailable()
        raise
    except OperationalError as exc:
        if _sqlstate(exc) == DEADLOCK_DETECTED:
            raise SlotUnavailable()
        raise

    _notify(booking, 'created')
    return booking


def change_status(booking_id, new_status, actor):
    """
    Customers may only cancel their own bookings, before the cancellation deadline.
    Admins may confirm, complete or cancel any booking.
    The row is locked so two concurrent status changes can't both win.
    """
    if new_status not in Booking.Status.values:
        raise ValidationError({'status': 'Unknown status.'})

    with transaction.atomic():
        booking = Booking.objects.select_for_update().filter(pk=booking_id).first()
        if booking is None or (booking.user_id != actor.pk and not is_admin(actor)):
            # Same answer for "doesn't exist" and "not yours": don't leak other users' bookings.
            raise NotFound('Booking not found.')

        if not booking.can_transition_to(new_status):
            raise ValidationError({'status': f'Cannot change status from {booking.status} to {new_status}.'})

        now = timezone.now()
        if not is_admin(actor):
            if new_status != Booking.Status.CANCELLED:
                raise PermissionDenied('You can only cancel your booking.')
            if booking.start_at - now < timedelta(hours=CANCELLATION_DEADLINE_HOURS):
                raise ValidationError({
                    'status': f'Bookings can be cancelled at least {CANCELLATION_DEADLINE_HOURS} hours in advance.'
                })

        if new_status == Booking.Status.COMPLETED and booking.start_at > now:
            raise ValidationError({'status': 'Cannot complete a booking that has not started yet.'})

        booking.status = new_status
        booking.save(update_fields=['status', 'updated_at'])
        _notify(booking, new_status)
        return booking


def expire_stale_pending_bookings():
    """Pending bookings nobody confirmed before their start time are cancelled."""
    now = timezone.now()
    return Booking.objects.filter(
        status=Booking.Status.PENDING,
        start_at__lte=now,
    ).update(status=Booking.Status.CANCELLED, updated_at=now)
