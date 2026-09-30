from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


class Employee(models.Model):
    name = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(8 * 60)],
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    employees = models.ManyToManyField(
        Employee,
        through='EmployeeService',
        related_name='services',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name='service_price_non_negative'),
            models.CheckConstraint(condition=Q(duration_minutes__gt=0), name='service_duration_positive'),
        ]

    def __str__(self):
        return self.name


class EmployeeService(models.Model):
    """Which employee can perform which service (N <-> N)."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employee_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='employee_services')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'service'], name='unique_employee_service'),
        ]

    def __str__(self):
        return f'{self.employee} - {self.service}'


class Availability(models.Model):
    """Weekly recurring working hours, in the business timezone (settings.TIME_ZONE)."""

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'availabilities'
        ordering = ['employee', 'day_of_week', 'start_time']
        constraints = [
            models.CheckConstraint(condition=Q(start_time__lt=F('end_time')), name='availability_start_before_end'),
            models.CheckConstraint(condition=Q(day_of_week__gte=0, day_of_week__lte=6), name='availability_valid_day'),
        ]
        indexes = [
            models.Index(fields=['employee', 'day_of_week']),
        ]

    def __str__(self):
        return f'{self.employee} {self.get_day_of_week_display()} {self.start_time}-{self.end_time}'

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('start_time must be before end_time.')

        # Two intervals overlap when each one starts before the other ends.
        overlapping = Availability.objects.filter(
            employee_id=self.employee_id,
            day_of_week=self.day_of_week,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError('This availability overlaps an existing one for the same day.')
