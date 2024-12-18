from project.rest_permissions import IsAdmin
from .models import Workflow
from .serializers import WorkflowSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from django.utils.timezone import now, timedelta
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Workflow


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

    @action(detail=False, methods=['get'])
    def get_dashboard_data(self, request):
        try:
            # Define the time periods for comparison
            current_week_start = now() - timedelta(days=now().weekday())
            last_week_start = current_week_start - timedelta(weeks=1)
            last_week_end = current_week_start

            # Count workflow changes for the current week
            current_week_changes = Workflow.objects.filter(
                updated_at__gte=current_week_start
            ).count()

            # Count workflow changes for the last week
            last_week_changes = Workflow.objects.filter(
                updated_at__gte=last_week_start,
                updated_at__lt=last_week_end
            ).count()

            # Calculate percentage change
            if last_week_changes == 0:
                percentage_change = 100 if current_week_changes > 0 else 0
            else:
                percentage_change = ((current_week_changes - last_week_changes) / last_week_changes) * 100

            # Prepare the response
            data = {
                "total": current_week_changes,
                "change": percentage_change,
            }

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred while fetching workflow data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
