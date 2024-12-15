from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import os
import google.generativeai as genai

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')
PARENT_FOLDER_ID = '1blDKeNNuJyO_HRrjXxxMyxDsajHH4t6A'


def authenticate():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    return service

def upload(file_path, file_name):
    service = authenticate()
    
    file_metadata = {
        'name': file_name,
        'parents': [PARENT_FOLDER_ID]
    }
    media = MediaFileUpload(file_path, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print(f"File '{file_name}' uploaded successfully. File ID: {file.get('id')}")

# Make sure to import MediaFileUpload

def summarize_document(filename: str):
    # Configure the Gemini API with your API key from the env file
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Create a prompt for the model
    prompt = (
        f"@Google Drive Generate a detailed and concise summary in the form of "
        f"a paragraph for the document titled: {filename}, ensuring the content "
        "is purely descriptive, highly detailed, and suitable for use as a database description. "
        "Please do not include in your response anything else and no need to say the doc name again."
    )

    # Generate a summary for the document
    summary = model.generate_content(prompt)

    try:
        summary_text = summary.candidates[0].content.parts[0].text
    except AttributeError as e:
        summary_text = None

    return summary_text
