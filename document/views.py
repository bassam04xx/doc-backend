from django.http import FileResponse
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from project.rest_permissions import IsAuthenticated, IsAdmin, IsManager, IsEmployee
from user.services.user_services import get_user_id
from .models import Document
from .serializers import DocumentSerializer
from .utils import (
    classify_document,
    download_file_from_drive,
    extract_text_from_pdf,
    upload,
    summarize_document,
    get_file_by_name
)
import tempfile


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
        summary = summarize_document(file_name)
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

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def integrateOldDocument(self, request):
        """
        Integrates an existing document into the system by creating a new Document record.
        Allowed for Admin and Manager only.
        """
        print("Integrating old document...")
        file_name = request.data.get('file_name')
        if not file_name:
            return Response({'error': 'File name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Metadata for the document
        owner_id = request.data.get('owner_id', 1)  # Default owner to admin
        category = request.data.get('category', 'Uncategorized')  # Default to 'Uncategorized'
        manager_id = request.data.get('manager_id', 1)  # Default manager to admin
        status_field = request.data.get('status', 'pending')  # Default status

        # Create and save the Document object
        document = Document.objects.create(
            owner_id=owner_id,
            category=category,
            manager_id=manager_id,
            summary="Summary not available for old documents.",
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
        print ("token", token)
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
           