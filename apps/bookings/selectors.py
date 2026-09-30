"""
Read-only booking queries (HackSoft styleguide: selectors fetch, services change).

Times: everything is stored in UTC. Availability hours are wall-clock times in the
business timezone (settings.TIME_ZONE), so slots are built in that timezone.
"""
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.bookings.models import Booking
from apps.services.models import Availability, Employee, Service

SLOT_STEP_MINUTES = getattr(settings, 'BOOKING_SLOT_STEP_MINUTES', 15)
BOOKING_HORIZON_DAYS = getattr(settings, 'BOOKING_HORIZON_DAYS', 60)


def business_tz():
    return timezone.get_default_timezone()


def is_admin(user):
    return bool(user and user.is_authenticated and user.is_business_admin)


def _overlaps(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


def get_available_slots(service_id, date, employee_id=None):
    """
    Free slots for a service on a local `date`, for one employee or all eligible ones.

    Slots are computed, not stored:
    availability windows of that weekday - active bookings - the past.
    A slot starts every SLOT_STEP_MINUTES from the window start and lasts
    service.duration_minutes; it must end inside the window.
    """
    service = Service.objects.filter(pk=service_id, is_active=True).first()
    if service is None:
        raise NotFound('Service not found.')

    now = timezone.now()
    today = timezone.localdate()
    if date < today or date > today + timedelta(days=BOOKING_HORIZON_DAYS):
        return []

    employees = Employee.objects.filter(is_active=True, employee_services__service=service)
    if employee_id is not None:
        employees = employees.filter(pk=employee_id)
    employees_by_id = {e.pk: e for e in employees}
    if not employees_by_id:
        return []

    employee_ids = list(employees_by_id)
    windows = Availability.objects.filter(
        employee_id__in=employee_ids,
        day_of_week=date.weekday(),
    ).order_by('start_time')

    tz = business_tz()
    day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()), tz)
    day_end = day_start + timedelta(days=1)
    busy = {}
    for booking in Booking.objects.filter(
        employee_id__in=employee_ids,
        status__in=Booking.ACTIVE_STATUSES,
        start_at__lt=day_end,
        end_at__gt=day_start,
    ).only('employee_id', 'start_at', 'end_at'):
        busy.setdefault(booking.employee_id, []).append((booking.start_at, booking.end_at))

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=SLOT_STEP_MINUTES)
    slots = []

    for window in windows:
        window_start = timezone.make_aware(datetime.combine(date, window.start_time), tz)
        window_end = timezone.make_aware(datetime.combine(date, window.end_time), tz)
        employee_busy = busy.get(window.employee_id, [])

        slot_start = window_start
        while slot_start + duration <= window_end:
            slot_end = slot_start + duration
            if slot_start > now and not any(
                _overlaps(slot_start, slot_end, b_start, b_end) for b_start, b_end in employee_busy
            ):
                slots.append({
                    'employee_id': window.employee_id,
                    'employee_name': employees_by_id[window.employee_id].name,
                    'start_at': slot_start,
                    'end_at': slot_end,
                })
            slot_start += step

    slots.sort(key=lambda s: (s['start_at'], s['employee_id']))
    return slots


def find_availability_window(employee, start_at, end_at):
    """
    The availability window that fully contains [start_at, end_at) on that local day,
    or None. A booking can't span midnight or two windows (e.g. across a lunch break).
    """
    tz = business_tz()
    local_start = timezone.localtime(start_at, tz)
    local_end = timezone.localtime(end_at, tz)
    if local_start.date() != local_end.date():
        return None
    return Availability.objects.filter(
        employee=employee,
        day_of_week=local_start.weekday(),
        start_time__lte=local_start.time(),
        end_time__gte=local_end.time(),
    ).first()


def get_booking_history(user, status=None, when=None):
    """
    Customer sees their own bookings, admin sees all.
    when: 'upcoming' | 'past' | None
    """
    qs = Booking.objects.select_related('service', 'employee', 'user')
    if not is_admin(user):
        qs = qs.filter(user=user)
    if status:
        qs = qs.filter(status=status)

    now = timezone.now()
    if when == 'upcoming':
        qs = qs.filter(start_at__gte=now).order_by('start_at')
    elif when == 'past':
        qs = qs.filter(start_at__lt=now).order_by('-start_at')
    return qs


def count_upcoming_bookings(employee):
    return Booking.objects.filter(
        employee=employee,
        status__in=Booking.ACTIVE_STATUSES,
        end_at__gt=timezone.now(),
    ).count()
    