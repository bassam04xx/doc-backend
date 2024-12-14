from rest_framework import viewsets
from .models import OldDocument
from .serializers import OldDocumentSerializer

class OldDocumentViewSet(viewsets.ModelViewSet):
    queryset = OldDocument.objects.all()
    serializer_class = OldDocumentSerializer
