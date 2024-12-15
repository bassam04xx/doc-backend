from django.shortcuts import render
from django.http import HttpResponse
from .utils import upload, summarize_document  # Ensure both are imported
from django.views.decorators.csrf import csrf_exempt
import tempfile
import os

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES['document']  # Correct the field name here
        
        # Save the file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Upload the file
        upload(temp_file_path, file.name)
        
        # Get the document summary
        summary = summarize_document(file.name)
        
        # Clean up the temporary file
        os.remove(temp_file_path)

        # Return the response with the summary
        return HttpResponse(f"File '{file.name}' uploaded successfully.<br/><br/>Summary:<br/>{summary}")
    else:
        return render(request, 'upload.html')  # Render the HTML page for GET request