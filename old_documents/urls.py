from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OldDocumentViewSet

router = DefaultRouter()
router.register(r'old_documents', OldDocumentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
