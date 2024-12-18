from django.db.models import Count
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from project.rest_permissions import IsAuthenticated, IsAdmin, IsManager, IsEmployee
from user.services.user_services import get_user_id, get_user_by_id, get_user_role
from .models import Document
from .serializers import DocumentSerializer
from .utils import (
    classify_document,
    download_file_from_drive,
    extract_text_from_pdf,
    upload,
    summarize_document,
    get_file_by_name, classify_custom_document, summarize_text, get_old_file_by_name
)
import tempfile
from graphql.execution import execute
from graphene_django.views import GraphQLView
from .schema import schema  # Assuming this schema is saved in 'graphql/schema.py'
from django.views.decorators.csrf import csrf_exempt


# Render form templates
def upload_document_form(request):
    return render(request, 'form.html')


def get_document_form(request):
    return render(request, 'get-document.html')


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin | IsEmployee])
    def upload_and_save(self, request):
        """
        Handles uploading a document, extracting its category and summary, 
        and saving it along with metadata. Allowed for Admin and Manager only.
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'File is required.'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = file.name
        print(f"Processing file: {file_name}")

        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        print('Extracting category...')
        category = classify_document(extract_text_from_pdf(temp_file_path))
        print(f"Category: {category}")

        print('Uploading file...')
        upload(temp_file_path, file_name)
        print('File uploaded successfully.')

        print('Generating summary...')
        summary = summarize_document(extract_text_from_pdf(temp_file_path))
        print(f"Summary: {summary}")

        # Collect metadata from the request
        token = request.headers.get('Authorization')
        token = token[len("Bearer "):]
        print(f"Token: {token}")
        owner_id = get_user_id(token)

        manager_id = request.data.get('manager_id', 1)  # Default manager to admin (ID: 1)

        # Create a Document object and save it to the database
        document = Document.objects.create(
            owner_id=owner_id,
            category=category,
            manager_id=manager_id,
            summary=summary,
            file_name=file_name,
            status="pending"
        )

        serializer = self.serializer_class(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_and_save_custom_document(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'File is required.'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = file.name
        print(f"Processing file: {file_name}")

        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        print('Extracting category...')
        category = classify_custom_document(extract_text_from_pdf(temp_file_path))
        print(f"Category: {category}")

        print('Generating summary...')
        summary = summarize_document(extract_text_from_pdf(temp_file_path))
        print(f"Summary: {summary}")

        print('Uploading file...')
        upload(temp_file_path, file_name)
        print('File uploaded successfully.')

        # Collect metadata from the request
        token = request.headers.get('Authorization')
        token = token[len("Bearer "):]
        print(f"Token: {token}")
        owner_id = get_user_id(token)

        manager_id = request.data.get('manager_id', 1)  # Default manager to admin (ID: 1)

        # Create a Document object and save it to the database
        document = Document.objects.create(
            owner_id=owner_id,
            category=category,
            manager_id=manager_id,
            summary=summary,
            file_name=file_name,
            status="pending"
        )

        serializer = self.serializer_class(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def get_document(self, request):
        """
        Fetches a document by its file name and returns it as a download.
        Allowed for Admin and Manager.
        """
        file_name = request.data.get('file_name')
        if not file_name:
            return Response({'error': 'File name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        file_id = get_file_by_name(file_name)
        if not file_id:
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

        print(f"Downloading file: {file_name}")
        file_io = download_file_from_drive(file_id)

        # Return the file as a downloadable response
        response = FileResponse(file_io, as_attachment=True, filename=file_name)
        return response

    @action(detail=False, methods=['post'])
    def integrateOldDocument(self, request):
        """
        Integrates an existing document into the system by creating a new Document record.
        Fetches the document from Google Drive by its file ID.
        Allowed for Admin and Manager only.
        """
        print("Integrating old document...")

        # Get the Google Drive file ID and file name from the request
        file_name = request.data.get('file_name')

        if not file_name:
            return Response({'error': 'File name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Download the file from Google Drive
        # Save the file temporarily
        file_io = get_old_file_by_name(file_name)

        if not file_io:
            return Response({'error': 'Failed to download file from Google Drive.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save the downloaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_io.read())  # Write the content (binary data) to the temp file
            temp_file_path = temp_file.name

        # Metadata for the document
        owner_id = request.data.get('owner_id', 1)  # Default owner to admin
        category = request.data.get('category', 'Uncategorized')  # Default to 'Uncategorized'
        manager_id = request.data.get('manager_id', 1)  # Default manager to admin
        status_field = request.data.get('status', 'pending')  # Default status

        # Extract summary and classify the document
        summary = summarize_document(extract_text_from_pdf(temp_file_path))

        # Create and save the Document object
        document = Document.objects.create(
            owner_id=owner_id,
            category=category,
            manager_id=manager_id,
            summary=summary,
            file_name=file_name,
            status=status_field
        )

        print(f"Document '{file_name}' integrated successfully.")
        serializer = self.serializer_class(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def get_documents_by_user_id(self, request):
        token = request.headers.get('Authorization')
        token = token[len("Bearer "):]
        user_id = get_user_id(token)
        print("user id", user_id)
        if user_id is None:
            return Response({'message': 'Invalid user ID.'}, status=status.HTTP_400_BAD_REQUEST)

        documents = Document.objects.filter(owner_id=user_id)
        print("documents", documents)
        if not documents.exists():
            return Response({'message': 'No documents found for this user'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(
            documents,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def get_documents_by_manager_id(self, request):
        token = request.headers.get('Authorization')

        token = token[len("Bearer "):]

        user_id = get_user_id(token)
        if user_id is None:
            return Response({'message': 'Invalid user ID.'}, status=status.HTTP_400_BAD_REQUEST)

        documents = Document.objects.filter(manager=user_id)
        if not documents.exists():
            return Response({'message': 'No documents found for this manager'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(
            documents,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_total_documents_data(self):
        """
        Calculates total documents for the current and last month, and percentage change.
        """
        current_time = timezone.now()
        first_day_this_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (first_day_this_month - timedelta(days=1)).replace(day=1)

        total_this_month = Document.objects.filter(created_at__gte=first_day_this_month).count()
        total_last_month = Document.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=first_day_this_month
        ).count()

        total_change = (
            0 if total_last_month == 0 else
            ((total_this_month - total_last_month) / total_last_month) * 100
        )

        return {
            "total": total_this_month,
            "change": round(total_change, 2)
        }

    def get_pending_documents_data(self):
        """
        Calculates pending documents for today and yesterday, and percentage change.
        """
        current_time = timezone.now()
        start_of_today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_yesterday = start_of_today - timedelta(days=1)

        pending_today = Document.objects.filter(
            created_at__gte=start_of_today, status="pending"
        ).count()
        pending_yesterday = Document.objects.filter(
            created_at__gte=start_of_yesterday,
            created_at__lt=start_of_today,
            status="pending"
        ).count()

        pending_change = (
            0 if pending_yesterday == 0 else
            ((pending_today - pending_yesterday) / pending_yesterday) * 100
        )

        return {
            "total": pending_today,
            "change": round(pending_change, 2)
        }

    def get_status_distribution_data(self):
        """
        Fetches the distribution of documents by their status.
        """
        status_distribution = Document.objects.values('status').annotate(count=Count('status'))
        return [
            {"name": entry["status"], "value": entry["count"]} for entry in status_distribution
        ]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def get_dashboard_data(self, request):
        """
        Fetches combined data for the admin dashboard in one request.
        """
        try:
            total_documents = self.get_total_documents_data()
            pending_documents = self.get_pending_documents_data()
            status_distribution = self.get_status_distribution_data()

            dashboard_data = {
                "total_documents": total_documents,
                "pending_documents": pending_documents,
                "status_distribution": status_distribution,
            }

            return Response(dashboard_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def recent_activity(self, request):
        """
        Fetch recent document activities, including the owner's details, action, document name, and timestamp.
        """
        # Fetch the most recent 10 documents (or you can adjust the limit)
        recent_documents = Document.objects.select_related('owner').order_by('-created_at')[:5]

        # Prepare the response data
        activities = [
            {
                "user": {
                    "name": doc.owner.get_full_name(),
                    "avatar":  None,
                    "initials": f"{doc.owner.first_name[0]}{doc.owner.last_name[0]}" if doc.owner.first_name else "",
                },
                "action": "uploaded",
                "document_name": doc.file_name,
                "time": doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for doc in recent_documents
        ]

        return Response(activities, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def get_top_managers(self, request):
        """
        Fetches the top managers based on the number of documents they manage.
        Returns manager's full name and the count of documents assigned to them.
        """
        # Aggregating document count for each manager
        managers = (
            Document.objects.values('manager_id')
            .annotate(document_count=Count('id'))
            .order_by('-document_count')[:5]  # Fetch top 10 managers
        )

        # Fetch the manager details
        top_managers = []
        for manager_data in managers:
            manager_id = manager_data['manager_id']
            document_count = manager_data['document_count']

            try:
                manager = get_user_by_id(manager_id)  # Use utility function to fetch manager details
                if manager:
                    top_managers.append({
                        "manager_id": manager.id,
                        "full_name": manager.get_full_name(),
                        "document_count": document_count
                    })
            except ValueError:
                # If the manager does not exist, skip adding to the result
                continue

        return Response(top_managers, status=status.HTTP_200_OK)

class GraphqlView(GraphQLView):
    schema = schema
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            # Here, you will handle the authentication token check
            token = request.headers.get('Authorization')
            if token:
                token = token[len("Bearer "):]
                # Verify the token and assign the user to the context if valid
                user_id = get_user_id(token)  # Assuming a helper function
                if user_id:
                    request.user.id = user_id  # Add user ID to request context
            else:
                return JsonResponse({'error': 'Authentication required'}, status=401)
        return super().dispatch(request, *args, **kwargs)