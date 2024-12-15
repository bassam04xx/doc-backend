
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, upload_document_form

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('upload-form/', upload_document_form, name='upload-document-form'),
    path('', include(router.urls)),  # This should include the `/documents/upload-and-save/` path
]