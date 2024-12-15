# views.py
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import render
from rest_framework import status, viewsets  # Make sure to import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Document
from .serializers import DocumentSerializer
from .utlis import upload, summarize_document , get_file_by_name
import tempfile

def upload_document_form(request):
    return render(request, 'form.html')
def get_document_form(request):
    return render(request, 'get-document.html')

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    # Inside DocumentViewSet class
    @action(detail=False, methods=['post'])
    def upload_and_save(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'File is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
        file_name = file.name
        print(file_name)
    
        # 1. Save the file using tempfile, which automatically uses the correct temporary directory
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
    
        print('uploading file...')
        # 2. Upload the file to Google Drive
        upload(temp_file_path, file_name)
        print('file uploaded')

        print('generating summary...')
    
        # 3. Generate the summary
        summary = summarize_document(file_name)
        print(summary)
    
        # Collect other data from the request
        owner_id = request.data.get('owner_id')
        category = request.data.get('category')
        manager_id = request.data.get('manager_id')
        status_field = request.data.get('status')
    
        # 4. Create a Document object with the summary and save it
        document = Document.objects.create(
            owner_id=owner_id,
            category=category,
            manager_id=manager_id,
            summary=summary,
            file_name=file_name,
            status=status_field
        )
    
        serializer = self.serializer_class(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @action(detail=False, methods=['post'])
    def get_document(self, request):
        file_name = request.data.get('file_name')
        file_url = get_file_by_name(file_name)  # Modify this to return the URL

        if not file_url:
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Redirect to the Google Drive file URL
        return HttpResponseRedirect(file_url)
    