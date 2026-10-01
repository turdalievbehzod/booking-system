from datetime import time, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.services.models import Availability, Employee, Service
from apps.users.models import User


class ServiceManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass-12345', role=User.Role.ADMIN)
        self.customer = User.objects.create_user('alice', 'alice@example.com', 'pass-12345')
        self.service = Service.objects.create(name='Haircut', duration_minutes=30, price=Decimal('100.00'))
        self.employee = Employee.objects.create(name='John', email='john@example.com')
        self.employee.services.add(self.service)

    def test_anyone_can_list_active_services(self):
        Service.objects.create(name='Old', duration_minutes=30, price=1, is_active=False)
        response = self.client.get('/api/v1/services/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([s['name'] for s in response.data['results']], ['Haircut'])
        self.assertEqual(response.data['results'][0]['employees'], [{'id': self.employee.pk, 'name': 'John'}])

    def test_only_admin_can_create_service(self):
        payload = {'name': 'Massage', 'duration_minutes': 60, 'price': '200.00'}
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.post('/api/v1/services/', payload).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post('/api/v1/services/', payload).status_code, 201)

    def test_service_validation(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/v1/services/', {'name': 'X', 'duration_minutes': 0, 'price': '-1'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data), {'duration_minutes', 'price'})

    def test_delete_service_deactivates_it(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f'/api/v1/services/{self.service.pk}/').status_code, 204)
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)

    def test_admin_assigns_services_to_employee(self):
        massage = Service.objects.create(name='Massage', duration_minutes=60, price=200)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f'/api/v1/employees/{self.employee.pk}/',
                                     {'service_ids': [self.service.pk, massage.pk]}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(set(self.employee.services.values_list('pk', flat=True)), {self.service.pk, massage.pk})

    def test_customers_do_not_see_employee_email(self):
        response = self.client.get('/api/v1/employees/')
        self.assertNotIn('email', response.data['results'][0])

    def test_cannot_deactivate_employee_with_upcoming_bookings(self):
        start = timezone.now() + timedelta(days=1)
        Booking.objects.create(user=self.customer, employee=self.employee, service=self.service,
                               start_at=start, end_at=start + timedelta(minutes=30), price=100)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f'/api/v1/employees/{self.employee.pk}/').status_code, 409)
        response = self.client.patch(f'/api/v1/employees/{self.employee.pk}/', {'is_active': False}, format='json')
        self.assertEqual(response.status_code, 409)


class AvailabilityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass-12345', role=User.Role.ADMIN)
        self.employee = Employee.objects.create(name='John', email='john@example.com')
        Availability.objects.create(employee=self.employee, day_of_week=0, start_time=time(9), end_time=time(13))
        self.client.force_authenticate(self.admin)

    def post(self, start, end, day=0):
        return self.client.post('/api/v1/availabilities/', {
            'employee': self.employee.pk, 'day_of_week': day, 'start_time': start, 'end_time': end,
        })

    def test_split_shift_is_allowed(self):
        self.assertEqual(self.post('14:00', '18:00').status_code, 201)  # lunch break 13-14

    def test_overlap_rejected(self):
        self.assertEqual(self.post('12:00', '15:00').status_code, 400)

    def test_start_after_end_rejected(self):
        self.assertEqual(self.post('18:00', '14:00').status_code, 400)

    def test_invalid_day_rejected(self):
        self.assertEqual(self.post('14:00', '18:00', day=7).status_code, 400)


class SeedDemoCommandTests(APITestCase):
    def seed(self):
        call_command('seed_demo', stdout=StringIO())

    def test_seeds_bookable_catalogue(self):
        self.seed()
        self.assertEqual(Service.objects.count(), 6)
        self.assertEqual(Employee.objects.count(), 4)
        # Every service has someone who provides it.
        self.assertFalse(Service.objects.filter(employees__isnull=True).exists())

        # The next Monday-to-Friday day has free slots for a haircut.
        day = timezone.localdate() + timedelta(days=1)
        while day.weekday() > 4:
            day += timedelta(days=1)
        haircut = Service.objects.get(name="Men's haircut")
        response = self.client.get('/api/v1/slots/', {'service_id': haircut.pk, 'date': day})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    def test_second_run_changes_nothing(self):
        self.seed()
        counts = (Service.objects.count(), Employee.objects.count(), Availability.objects.count())
        self.seed()
        self.assertEqual(counts, (Service.objects.count(), Employee.objects.count(), Availability.objects.count()))

    def test_skips_when_catalogue_exists(self):
        Service.objects.create(name='Own service', duration_minutes=30, price=Decimal('1.00'))
        self.seed()
        self.assertEqual(Service.objects.count(), 1)
        self.assertFalse(Employee.objects.exists())
