"""
Demo catalogue: services, employees and weekly working hours for a small salon.

Runs on every start of the demo deployment (no shell on the free plan), so it only
seeds an empty catalogue: once any service exists, nothing is added or changed,
and whatever the admin edits or deactivates stays that way.
"""
from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.services.models import Availability, Employee, Service

SERVICES = [
    # name, description, duration (min), price (UZS)
    ("Men's haircut", 'Classic or modern cut, wash and styling.', 30, '80000'),
    ('Beard trim', 'Shaping, trimming and hot towel.', 20, '50000'),
    ('Haircut + beard', 'Full haircut and beard grooming in one visit.', 45, '120000'),
    ('Hair colouring', 'Single-tone colouring with a consultation.', 90, '250000'),
    ('Manicure', 'Nail shaping, cuticle care and polish.', 60, '150000'),
    ('Relaxing massage', 'Full-body massage with aromatic oils.', 60, '300000'),
]

# Weekdays: Mon=0 ... Sun=6.
MON_FRI = range(0, 5)
MON_SAT = range(0, 6)
TUE_SAT = range(1, 6)

EMPLOYEES = [
    # name, email, services, working days, daily windows (a lunch break = two windows)
    ('Aziz Karimov', 'aziz@studio.example', ["Men's haircut", 'Beard trim', 'Haircut + beard'],
     MON_SAT, [(time(9), time(13)), (time(14), time(18))]),
    ('Jasur Toshmatov', 'jasur@studio.example', ["Men's haircut", 'Beard trim', 'Haircut + beard', 'Hair colouring'],
     TUE_SAT, [(time(10), time(19))]),
    ('Malika Yusupova', 'malika@studio.example', ['Hair colouring', 'Manicure'],
     MON_FRI, [(time(9), time(13)), (time(14), time(17))]),
    ('Dilnoza Rakhimova', 'dilnoza@studio.example', ['Manicure', 'Relaxing massage'],
     MON_SAT, [(time(11), time(20))]),
]


class Command(BaseCommand):
    help = 'Seed demo services, employees and working hours if the catalogue is empty.'

    @transaction.atomic
    def handle(self, *args, **options):
        if Service.objects.exists():
            self.stdout.write('seed_demo: services already exist, nothing to do.')
            return

        services = {
            name: Service.objects.create(
                name=name, description=description, duration_minutes=minutes, price=Decimal(price),
            )
            for name, description, minutes, price in SERVICES
        }

        for name, email, service_names, days, windows in EMPLOYEES:
            employee, _ = Employee.objects.get_or_create(email=email, defaults={'name': name})
            employee.services.add(*(services[s] for s in service_names))
            Availability.objects.bulk_create(
                Availability(employee=employee, day_of_week=day, start_time=start, end_time=end)
                for day in days
                for start, end in windows
                if not employee.availabilities.filter(day_of_week=day).exists()
            )

        self.stdout.write(
            f'seed_demo: created {len(services)} services, {len(EMPLOYEES)} employees and their working hours.'
        )
