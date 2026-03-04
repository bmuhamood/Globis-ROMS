from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.dashboard, name='dashboard'),
    path('accounts/', include('apps.accounts.urls')),
    path('clients/', include('apps.clients.urls')),
    path('agents/', include('apps.agents.urls')),
    path('candidates/', include('apps.candidates.urls')),
    path('documents/', include('apps.documents.urls')),
    path('visa/', include('apps.visa_process.urls')),
    path('payments/', include('apps.candidate_payments.urls')),
    path('placements/', include('apps.placements.urls')),
    path('finance/', include('apps.finance.urls')),
    path('reports/', include('apps.reports.urls')),
    path('imports/', include('apps.imports.urls')),
    path('jobs/', include('apps.jobs.urls')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)