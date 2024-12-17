from decouple import config
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import google.generativeai as genai
from requests import HTTPError
import io
import PyPDF2
from transformers import pipeline

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')
PARENT_FOLDER_ID = config('PARENT_FOLDER_ID')


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

    # Upload the file
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = file.get('id')

    # Set file permissions to "Anyone with the link can view"
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    service.permissions().create(
        fileId=file_id,
        body=permission
    ).execute()

    print(f"File '{file_name}' uploaded successfully. File ID: {file_id}")

    return file_id  # Return the file ID if needed


# Make sure to import MediaFileUpload

def summarize_document(filename: str):
    # Configure the Gemini API with your API key from the env file
    genai.configure(api_key=config('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Create a prompt for the model
    prompt = (
        f"@Google Drive Generate a detailed and concise summary  in the form of a paragraphe for the document titled : {filename}. ensurin g the content is purely descriptive, highly detailed, and suitable for use as a database description. please do not include in your response anything else and no need to say the doc name again. i want to mention the exact name and values  in the summary"
    )

    # Generate a summary for the document
    summary = model.generate_content(prompt)

    try:
        summary_text = summary.candidates[0].content.parts[0].text
    except AttributeError as e:
        summary_text = None

    return summary_text


def get_file_by_name(filename):
    service = authenticate()
    try:
        # Use the files().list() method to search for files by name
        results = service.files().list(
            q=f"name = '{filename}' and trashed = false",
            spaces='drive',
            fields="files(id, name)",
        ).execute()

        files = results.get('files', [])

        if not files:
            print("No files found.")
            return None

        # Return only the file ID
        return files[0]['id']

    except HTTPError as error:
        print(f"An error occurred: {error}")
        return None


def download_file_from_drive(file_id):
    service = authenticate()
    request = service.files().get_media(fileId=file_id)
    file_io = io.BytesIO()
    downloader = MediaIoBaseDownload(file_io, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download progress: {int(status.progress() * 100)}%")

    file_io.seek(0)
    return file_io


def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text


def classify_document(text: str) -> str:
    # Predefined categories
    categories = ["report", "contract", "invoice", "day-off"]

    # Validate input
    if not text or not isinstance(text, str):
        raise ValueError("Input text must be a non-empty string.")
    if not categories:
        raise ValueError("Categories list must contain at least one label.")

    # Load a pre-trained zero-shot classification pipeline from Hugging Face
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    # Perform classification
    result = classifier(text, candidate_labels=categories)

    predicted_category = result['labels'][0]
    return predicted_category

