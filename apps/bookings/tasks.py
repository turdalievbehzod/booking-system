from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.bookings.models import Booking
from apps.bookings.services import expire_stale_pending_bookings

EMAIL_SUBJECTS = {
    'created': 'Booking received',
    Booking.Status.CONFIRMED: 'Booking confirmed',
    Booking.Status.CANCELLED: 'Booking cancelled',
    Booking.Status.COMPLETED: 'Thank you for your visit',
}


@shared_task
def expire_stale_pending_bookings_task():
    return expire_stale_pending_bookings()


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_booking_email(booking_id, event):
    booking = Booking.objects.select_related('user', 'service', 'employee').filter(pk=booking_id).first()
    if booking is None or not booking.user.email:
        return

    start = timezone.localtime(booking.start_at)
    send_mail(
        subject=EMAIL_SUBJECTS.get(event, 'Booking update'),
        message=(
            f'Hello {booking.user.first_name or booking.user.username},\n\n'
            f'Service: {booking.service.name}\n'
            f'Employee: {booking.employee.name}\n'
            f'Time: {start:%Y-%m-%d %H:%M} ({settings.TIME_ZONE})\n'
            f'Price: {booking.price}\n'
            f'Status: {booking.get_status_display()}\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
    )
