
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, upload_document_form, get_document_form
from graphene_django.views import GraphQLView


router = DefaultRouter()
router.register(r'', DocumentViewSet, basename='document')

urlpatterns = [
    path('upload-form/', upload_document_form, name='upload-document-form'),
    path('get-form/', get_document_form, name='get-document-form'),
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    path('', include(router.urls)),  # This should include the `/documents/upload-and-save/` path
]