# views.py
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import render
from rest_framework import status, viewsets  # Make sure to import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Document
from .serializers import DocumentSerializer
from .utlis import classify_document, download_file_from_drive, extract_text_from_pdf, upload, summarize_document , get_file_by_name
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
        
        print('getting the category...')
        # 2. Get the category
        category = classify_document(extract_text_from_pdf(temp_file_path))
        print(category)
    
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
        manager_id = request.data.get('manager_id')
        status_field = request.data.get('status')
    
        # 4. Create a Document object with the summary and save it
        document = Document.objects.create(
            owner_id=1,
            category=category,
            manager_id=1,
            summary=summary,
            file_name=file_name,
            status="pending"
        )
    
        serializer = self.serializer_class(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    @action(detail=False, methods=['post'])  
    def get_document(self, request):
        file_name = request.data.get('file_name')
        file_id = get_file_by_name(file_name)

        if not file_id:
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Download the file from Google Drive
        file_io = download_file_from_drive(file_id)

        # Return the file as a download

        response = FileResponse(file_io, as_attachment=True, filename=file_name)
        return response
    

    @action(detail=False, methods=['post'])
    def integrateOldDocument(self, request):
        print(request.data)
        file_name = request.data.get('file_name')
        # file_id = get_file_by_name(file_name)
        # print(file_id)

        # if not file_id:
        #      return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # summary = summarize_document(file_name)
        owner_id = request.data.get('owner_id')
        category = request.data.get('category')
        manager_id = 1
        status_field = request.data.get('status')

        document = Document.objects.create(
            owner_id=owner_id,
            category=category,
            manager_id=manager_id,
            summary="summary",
            file_name=file_name,
            status=status_field
        )

        serializer = self.serializer_class(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)