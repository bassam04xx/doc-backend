from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OldDocumentViewSet

router = DefaultRouter()
router.register(r'', OldDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
