from django.contrib import admin
from .models import Candidate

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'passport_no', 'position', 'agent', 'client', 'created_at')
    list_filter = ('agent', 'client', 'created_at')
    search_fields = ('full_name', 'passport_no', 'contact_number')
    date_hierarchy = 'created_at'