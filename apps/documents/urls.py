from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('missing/', views.missing_documents, name='missing_documents'),
    path('<int:pk>/update/', views.document_update, name='document_update'),

    # New document upload URLs
    path('candidate/<int:candidate_id>/', views.candidate_documents, name='candidate_documents'),
    path('upload/<int:candidate_id>/', views.upload_document, name='upload_document'),
    path('download/<int:document_id>/', views.download_document, name='download_document'),
    path('view/<int:document_id>/', views.view_document, name='view_document'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('merge/<int:candidate_id>/', views.merge_documents, name='merge_documents'),
    path('download-merged/<int:candidate_id>/', views.download_merged, name='download_merged'),
    path('init-types/', views.initialize_document_types, name='init_document_types'),
    path('documents/bulk-delete/<int:candidate_id>/', views.bulk_delete_documents, name='bulk_delete_documents'),
    path('documents/download-all/<int:candidate_id>/', views.download_all_documents, name='download_all_documents'),
]