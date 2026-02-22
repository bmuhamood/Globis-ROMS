from django.apps import AppConfig
import os

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        from django.contrib.auth.models import User
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if username and password and not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)