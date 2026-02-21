from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Ensures a superuser exists based on environment variables'

    def handle(self, *args, **options):
        # Get credentials from environment variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        # Check if all required variables are set
        if not username or not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    'Superuser not created. Missing environment variables:\n'
                    'DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD'
                )
            )
            return

        # Check if superuser already exists
        if not User.objects.filter(username=username).exists():
            # Create the superuser
            User.objects.create_superuser(username, email, password)
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully')
            )
        else:
            self.stdout.write(f'Superuser "{username}" already exists')