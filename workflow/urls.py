
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet
router = DefaultRouter()
router.register(r'', WorkflowViewSet, basename='workflow')

urlpatterns = [
  
    path('', include(router.urls)),  # This should include the `/documents/upload-and-save/` path
]