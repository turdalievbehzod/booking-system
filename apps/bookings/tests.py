import threading
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core import mail
from django.db import IntegrityError, connection, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.bookings.services import SlotUnavailable, create_booking, expire_stale_pending_bookings
from apps.services.models import Availability, Employee, Service
from apps.users.models import User


def local_dt(date, hour, minute=0):
    return timezone.make_aware(datetime.combine(date, time(hour, minute)))


class BookingFixtureMixin:
    """Service (30 min) done by two employees, both working every day 09:00-18:00."""

    def create_fixture(self):
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass-12345', role=User.Role.ADMIN)
        self.alice = User.objects.create_user('alice', 'alice@example.com', 'pass-12345')
        self.bob = User.objects.create_user('bob', 'bob@example.com', 'pass-12345')

        self.service = Service.objects.create(name='Haircut', duration_minutes=30, price=Decimal('100000.00'))
        self.other_service = Service.objects.create(name='Massage', duration_minutes=60, price=Decimal('200000.00'))
        self.emp1 = Employee.objects.create(name='John', email='john@example.com')
        self.emp2 = Employee.objects.create(name='Kate', email='kate@example.com')
        self.emp1.services.add(self.service)
        self.emp2.services.add(self.service)
        for employee in (self.emp1, self.emp2):
            for day in range(7):
                Availability.objects.create(employee=employee, day_of_week=day, start_time=time(9), end_time=time(18))

        self.day = timezone.localdate() + timedelta(days=1)
        self.ten_am = local_dt(self.day, 10)

    def make_booking(self, user=None, employee=None, start_at=None, minutes=30, status=Booking.Status.CONFIRMED):
        start_at = start_at or self.ten_am
        return Booking.objects.create(
            user=user or self.alice, employee=employee or self.emp1, service=self.service,
            start_at=start_at, end_at=start_at + timedelta(minutes=minutes),
            price=self.service.price, status=status,
        )


class SlotsApiTests(BookingFixtureMixin, APITestCase):
    def setUp(self):
        self.create_fixture()

    def get_slots(self, **params):
        return self.client.get('/api/v1/slots/', {'service_id': self.service.pk, 'date': self.day, **params})

    def test_slots_are_public_and_cover_working_hours(self):
        response = self.get_slots(employee_id=self.emp1.pk)
        self.assertEqual(response.status_code, 200)
        # 09:00..17:30 every 15 minutes -> 35 slots, the last one ends exactly at 18:00.
        self.assertEqual(len(response.data), 35)
        self.assertEqual(timezone.localtime(datetime.fromisoformat(response.data[-1]['end_at'])).time(), time(18))

    def test_booked_time_is_not_offered(self):
        self.make_booking(start_at=self.ten_am)
        starts = {s['start_at'] for s in self.get_slots(employee_id=self.emp1.pk).data}
        # 09:45, 10:00, 10:15 would overlap 10:00-10:30.
        for blocked in (local_dt(self.day, 9, 45), self.ten_am, local_dt(self.day, 10, 15)):
            self.assertNotIn(blocked.isoformat(), starts)
        self.assertIn(local_dt(self.day, 10, 30).isoformat(), starts)

    def test_cancelled_booking_frees_the_slot(self):
        self.make_booking(start_at=self.ten_am, status=Booking.Status.CANCELLED)
        starts = {s['start_at'] for s in self.get_slots(employee_id=self.emp1.pk).data}
        self.assertIn(self.ten_am.isoformat(), starts)

    def test_past_date_returns_nothing(self):
        response = self.client.get('/api/v1/slots/', {
            'service_id': self.service.pk, 'date': timezone.localdate() - timedelta(days=1),
        })
        self.assertEqual(response.data, [])

    def test_inactive_service_is_not_found(self):
        self.service.is_active = False
        self.service.save()
        self.assertEqual(self.get_slots().status_code, 404)


class CreateBookingApiTests(BookingFixtureMixin, APITestCase):
    def setUp(self):
        self.create_fixture()
        self.client.force_authenticate(self.alice)

    def book(self, **overrides):
        payload = {'service_id': self.service.pk, 'employee_id': self.emp1.pk, 'start_at': self.ten_am.isoformat()}
        payload.update(overrides)
        return self.client.post('/api/v1/bookings/', payload, format='json')

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.book().status_code, 401)

    def test_creates_pending_booking_with_snapshots_and_sends_email(self):
        # Emails are queued with transaction.on_commit, which TestCase never commits.
        with self.captureOnCommitCallbacks(execute=True):
            response = self.book()
        self.assertEqual(response.status_code, 201, response.data)
        booking = Booking.objects.get(pk=response.data['id'])
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.end_at, self.ten_am + timedelta(minutes=30))
        self.assertEqual(booking.price, self.service.price)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['alice@example.com'])

        # Changing the service later doesn't rewrite the booking.
        self.service.price = Decimal('1.00')
        self.service.duration_minutes = 90
        self.service.save()
        booking.refresh_from_db()
        self.assertEqual(booking.price, Decimal('100000.00'))
        self.assertEqual(booking.end_at, self.ten_am + timedelta(minutes=30))

    def test_double_booking_returns_409(self):
        self.make_booking(user=self.bob, start_at=local_dt(self.day, 10, 15))
        response = self.book()
        self.assertEqual(response.status_code, 409)

    def test_other_employee_is_still_bookable_at_same_time(self):
        self.make_booking(user=self.bob, employee=self.emp1)
        self.assertEqual(self.book(employee_id=self.emp2.pk).status_code, 201)

    def test_customer_cannot_overlap_own_bookings(self):
        self.make_booking(user=self.alice, employee=self.emp2)
        response = self.book(employee_id=self.emp1.pk)
        self.assertEqual(response.status_code, 400)

    def test_employee_must_provide_service(self):
        response = self.book(service_id=self.other_service.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn('employee_id', response.data)

    def test_outside_working_hours(self):
        self.assertEqual(self.book(start_at=local_dt(self.day, 8).isoformat()).status_code, 400)
        # Starts inside hours but would end after 18:00.
        self.assertEqual(self.book(start_at=local_dt(self.day, 17, 45).isoformat()).status_code, 400)

    def test_start_must_be_on_slot_grid(self):
        self.assertEqual(self.book(start_at=local_dt(self.day, 10, 7).isoformat()).status_code, 400)

    def test_past_and_too_far_future(self):
        past = local_dt(timezone.localdate() - timedelta(days=1), 10)
        self.assertEqual(self.book(start_at=past.isoformat()).status_code, 400)
        far = local_dt(timezone.localdate() + timedelta(days=90), 10)
        self.assertEqual(self.book(start_at=far.isoformat()).status_code, 400)

    def test_inactive_employee(self):
        self.emp1.is_active = False
        self.emp1.save()
        self.assertEqual(self.book().status_code, 400)

    def test_missing_fields(self):
        response = self.client.post('/api/v1/bookings/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data), {'service_id', 'employee_id', 'start_at'})


class BookingStatusApiTests(BookingFixtureMixin, APITestCase):
    def setUp(self):
        self.create_fixture()
        self.booking = self.make_booking(status=Booking.Status.PENDING)

    def post(self, user, action, booking=None):
        self.client.force_authenticate(user)
        return self.client.post(f'/api/v1/bookings/{(booking or self.booking).pk}/{action}/')

    def test_owner_can_cancel(self):
        response = self.post(self.alice, 'cancel')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], Booking.Status.CANCELLED)

    def test_other_customer_gets_404(self):
        self.assertEqual(self.post(self.bob, 'cancel').status_code, 404)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f'/api/v1/bookings/{self.booking.pk}/').status_code, 404)

    def test_customer_cannot_confirm(self):
        self.assertEqual(self.post(self.alice, 'confirm').status_code, 403)

    def test_admin_confirms_then_completes_only_after_start(self):
        self.assertEqual(self.post(self.admin, 'confirm').status_code, 200)
        self.assertEqual(self.post(self.admin, 'complete').status_code, 400)  # hasn't started

        past = self.make_booking(start_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(self.post(self.admin, 'complete', past).status_code, 200)

    def test_invalid_transition(self):
        self.post(self.alice, 'cancel')
        self.assertEqual(self.post(self.admin, 'confirm').status_code, 400)

    def test_cancellation_deadline_applies_to_customer_not_admin(self):
        soon = self.make_booking(start_at=timezone.now() + timedelta(hours=1), user=self.bob)
        self.assertEqual(self.post(self.bob, 'cancel', soon).status_code, 400)
        self.assertEqual(self.post(self.admin, 'cancel', soon).status_code, 200)


class BookingHistoryApiTests(BookingFixtureMixin, APITestCase):
    def setUp(self):
        self.create_fixture()
        self.mine_upcoming = self.make_booking(user=self.alice)
        self.mine_past = self.make_booking(user=self.alice, start_at=timezone.now() - timedelta(days=3),
                                           status=Booking.Status.COMPLETED)
        self.others = self.make_booking(user=self.bob, employee=self.emp2)

    def ids(self, user, **params):
        self.client.force_authenticate(user)
        response = self.client.get('/api/v1/bookings/', params)
        self.assertEqual(response.status_code, 200)
        return {b['id'] for b in response.data['results']}

    def test_customer_sees_only_own(self):
        self.assertEqual(self.ids(self.alice), {self.mine_upcoming.pk, self.mine_past.pk})

    def test_filters(self):
        self.assertEqual(self.ids(self.alice, when='upcoming'), {self.mine_upcoming.pk})
        self.assertEqual(self.ids(self.alice, when='past'), {self.mine_past.pk})
        self.assertEqual(self.ids(self.alice, status='completed'), {self.mine_past.pk})

    def test_admin_sees_all(self):
        self.assertEqual(len(self.ids(self.admin)), 3)


class ExpirePendingTests(BookingFixtureMixin, APITestCase):
    def setUp(self):
        self.create_fixture()

    def test_unconfirmed_pending_booking_expires_after_start(self):
        stale = self.make_booking(start_at=timezone.now() - timedelta(minutes=5), status=Booking.Status.PENDING)
        future = self.make_booking(status=Booking.Status.PENDING, employee=self.emp2)
        self.assertEqual(expire_stale_pending_bookings(), 1)
        stale.refresh_from_db()
        future.refresh_from_db()
        self.assertEqual(stale.status, Booking.Status.CANCELLED)
        self.assertEqual(future.status, Booking.Status.PENDING)


class DatabaseConstraintTests(BookingFixtureMixin, APITestCase):
    """The DB itself refuses overlaps, even when application checks are bypassed."""

    def setUp(self):
        self.create_fixture()

    def test_overlap_rejected_by_exclusion_constraint(self):
        self.make_booking(start_at=self.ten_am)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_booking(user=self.bob, start_at=local_dt(self.day, 10, 15))

    def test_back_to_back_bookings_are_allowed(self):
        self.make_booking(start_at=self.ten_am)
        self.make_booking(user=self.bob, start_at=self.ten_am + timedelta(minutes=30))  # [10:00,10:30) + [10:30,11:00)

    def test_cancelled_booking_does_not_block(self):
        self.make_booking(start_at=self.ten_am, status=Booking.Status.CANCELLED)
        self.make_booking(user=self.bob, start_at=self.ten_am)


class ConcurrentBookingTests(BookingFixtureMixin, TransactionTestCase):
    """
    Two users book the same slot at the same moment. Both pass the application-level
    "is it free?" check; the exclusion constraint lets exactly one insert through.
    """

    def setUp(self):
        self.create_fixture()

    def test_only_one_of_simultaneous_requests_wins(self):
        users = [User.objects.create_user(f'user{i}', f'user{i}@example.com', 'pass-12345') for i in range(5)]
        barrier = threading.Barrier(len(users))
        results = []

        def attempt(user):
            try:
                barrier.wait()
                create_booking(user, self.service.pk, self.emp1.pk, self.ten_am)
                results.append('ok')
            except SlotUnavailable:
                results.append('conflict')
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt, args=(u,)) for u in users]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(results.count('ok'), 1, results)
        self.assertEqual(results.count('conflict'), len(users) - 1, results)
        self.assertEqual(Booking.objects.filter(employee=self.emp1, start_at=self.ten_am).count(), 1)
