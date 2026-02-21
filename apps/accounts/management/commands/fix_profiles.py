from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Fix user profiles and set superusers to admin role'

    def handle(self, *args, **options):
        users = User.objects.all()
        fixed_count = 0
        
        for user in users:
            # Create profile if it doesn't exist
            if not hasattr(user, 'profile'):
                profile = UserProfile.objects.create(user=user)
                self.stdout.write(f"Created profile for {user.username}")
            else:
                profile = user.profile
            
            # If user is superuser, set role to admin
            if user.is_superuser and profile.role != 'admin':
                old_role = profile.role
                profile.role = 'admin'
                profile.can_add_candidates = True
                profile.can_edit_candidates = True
                profile.can_delete_candidates = True
                profile.can_add_agents = True
                profile.can_edit_agents = True
                profile.can_delete_agents = True
                profile.can_add_clients = True
                profile.can_edit_clients = True
                profile.can_delete_clients = True
                profile.can_view_finance = True
                profile.can_add_income = True
                profile.can_add_expense = True
                profile.can_view_reports = True
                profile.can_view_finance_reports = True
                profile.can_import = True
                profile.can_export = True
                profile.save()
                self.stdout.write(f"Fixed superuser {user.username}: changed role from {old_role} to admin")
                fixed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully fixed {fixed_count} superuser profiles'))