from rest_framework import viewsets
from .models import OldDocument
from .serializers import OldDocumentSerializer

import logging

logger = logging.getLogger(__name__)

class OldDocumentViewSet(viewsets.ModelViewSet):
    queryset = OldDocument.objects.all()
    serializer_class = OldDocumentSerializer

    def partial_update(self, request, *args, **kwargs):
        logger.debug(f"PATCH request data: {request.data}")
        return super().partial_update(request, *args, **kwargs)
