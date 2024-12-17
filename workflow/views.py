from .models import Workflow
from .serializers import WorkflowSerializer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer

    @action(detail=False, methods=['get'])
    def get_workflows_by_document_id(self, request):
        document_id = request.query_params.get('document_id')
        if not document_id:
            return Response({'message': 'Document ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        workflows = Workflow.objects.filter(document_id=document_id)
        if not workflows.exists():
            return Response({'message': 'No workflows found for this document'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(
            workflows,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)