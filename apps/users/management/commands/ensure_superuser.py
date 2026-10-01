"""
Create the business admin account from DJANGO_SUPERUSER_* environment variables.

Runs on every start of hosts without a shell (Render free plan), so it must be
idempotent and must never stop the server from starting: problems are printed
to the logs with the reason instead of failing silently.
"""
import os

from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = 'Create the admin from DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD if it does not exist.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip().lower()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

        user = User.objects.filter(username=username).first() if username else None
        if user is not None:
            # Never promote an existing account: anyone can self-register a username,
            # so promoting by name would hand admin rights to whoever registered it first.
            if user.is_superuser:
                self.stdout.write(f'ensure_superuser: admin "{username}" already exists.')
            else:
                self.stderr.write(
                    f'ensure_superuser: NOT created, username "{username}" belongs to a regular account. '
                    'Set DJANGO_SUPERUSER_USERNAME to a different name.'
                )
            return

        missing = [name for name, value in [
            ('DJANGO_SUPERUSER_USERNAME', username),
            ('DJANGO_SUPERUSER_EMAIL', email),
            ('DJANGO_SUPERUSER_PASSWORD', password),
        ] if not value]
        if missing:
            self.stdout.write(f'ensure_superuser: skipped, not set: {", ".join(missing)}.')
            return

        if User.objects.filter(email__iexact=email).exists():
            self.stderr.write(
                f'ensure_superuser: NOT created, email "{email}" is already used by another account. '
                'Set DJANGO_SUPERUSER_EMAIL to a different address.'
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(f'ensure_superuser: created admin "{username}".')
