from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    
    # REMOVED the ready() method - superuser creation will be handled
    # by a management command during deployment instead