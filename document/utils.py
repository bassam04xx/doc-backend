from decouple import config
from django.contrib.auth import get_user_model
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import google.generativeai as genai
from requests import HTTPError
import io
import PyPDF2
from transformers import pipeline
from .models import Document
from stable_baselines3 import PPO  # Exemple de modèle RL
import numpy as np

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

def summarize_document(document_text: str):
    # Configure the Gemini API with your API key from the env file
    genai.configure(api_key=config('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    print("document text", document_text)

    # Create a prompt for the model
    prompt = (
        f"{document_text} Generate a detailed and concise summary  in the form of a paragraphe for the document titled . ensurin g the content is purely descriptive, highly detailed, and suitable for use as a database description. please do not include in your response anything else and no need to say the doc name again. i want to mention the exact name and values  in the summary"
    )

    # Generate a summary for the document
    summary = model.generate_content(prompt)

    try:
        summary_text = summary.candidates[0].content.parts[0].text
    except AttributeError as e:
        summary_text = None

    return summary_text


def transform_text_to_pgsql_command(text):
    # Get table schema dynamically from the Document model
    schema = []
    for field in Document._meta.fields:
        column_name = field.name
        column_type = type(field).__name__
        schema.append(f"{column_name} ({column_type})")
    table_schema = ", ".join(schema)

    # Configure the genai API
    genai.configure(api_key=config("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prompt construction
    prompt = (
        f"You are a PostgreSQL expert. Given an input table schema and a question, "
        f"generate a valid PostgreSQL query to answer the question. "
        f"The question is: {text} and the table schema is as follows:\n"

        f"Table 'documents':\n"
        f"  - id (PK, INT)\n"
        f"  - owner_id (FK to users.id, INT)\n"
        f"  - category (VARCHAR, can be 'invoice', 'day-off', 'report')\n"
        f"  - manager_id (FK to users.id, INT)\n"
        f"  - summary (TEXT)\n"
        f"  - file_name (VARCHAR)\n"
        f"  - created_at (DATETIME)\n"
        f"  - status (VARCHAR)\n"

        f"Table 'users':\n"
        f"  - id (PK, INT)\n"
        f"  - username (VARCHAR)\n"
        f"  - email (VARCHAR, UNIQUE)\n"
        f"  - role (VARCHAR, choices: 'admin', 'manager', 'employee')\n"
        f"  - manager_type (TEXT, optional, for 'manager' role)\n"

        f"Table 'workflow':\n"
        f"  - id (PK, INT)\n"
        f"  - document_id (FK to documents.id, INT)\n"
        f"  - former_status (VARCHAR)\n"
        f"  - new_status (VARCHAR)\n"
        f"  - updated_at (DATETIME)\n"
        f"  - updated_by_id (FK to users.id, INT)\n"

        f"Relations:\n"
        f"  - 'documents.owner_id' references 'users.id'\n"
        f"  - 'documents.manager_id' references 'users.id'\n"
        f"  - 'workflow.document_id' references 'documents.id'\n"
        f"  - 'workflow.updated_by_id' references 'users.id'\n"

        f"IMPORTANT: ONLY GIVE THE PGSQL COMMAND, DO NOT SAY ANYTHING ELSE."
    )

    # Generate the PostgreSQL command
    try:
        pgsql_command = model.generate_content(prompt).candidates[0].content.parts[0].text
        return pgsql_command
    except Exception as e:
        return f"Error generating PostgreSQL command: {e}"


def get_old_file_by_name(filename):
    service = authenticate()  # Assuming authenticate() sets up the Google API client
    try:
        # Use the files().list() method to search for files by name
        results = service.files().list(
            q=f"name = '{filename}' and trashed = false",
            spaces='drive',
            fields="files(id, name)"
        ).execute()

        files = results.get('files', [])

        if not files:
            print("No files found.")
            return None

        # Fetch the file content using its ID
        file_id = files[0]['id']

        # Get the media content of the file (this returns a MediaIoBaseDownload object)
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()  # Create an in-memory byte stream
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Return the binary data
        file_io.seek(0)  # Reset stream position to the beginning
        return file_io

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


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


def classify_custom_document(text: str) -> str:
    categories = [
        "Documentation", "Design", "Proposal", "Memo", "Agreement", "Receipt", "Letter",
        "Manual", "Presentation", "Email", "Resume", "Minutes", "Checklist", "Policy", "Procedure",
        "Research Paper", "Whitepaper", "Guideline", "Testimonial", "Certificate", "Order",
        "SOW (Statement of Work)", "Project Plan", "Budget", "Financial Statement", "Contract Amendment",
        "Project Update", "Job Description", "Non-disclosure Agreement (NDA)", "Tender", "Legal Notice",
        "Patent", "Press Release", "Event Flyer", "Newsletter", "Statement", "Application Form", "Transcript",
        "Report Summary", "Project Charter", "Presentation Slides", "Terms and Conditions", "Agreement Addendum",
        "Purchase Order", "Order Confirmation", "Business Letter", "Letter of Intent", "Internal Memo",
        "Customer Feedback", "Work Order", "Audit Report", "Risk Assessment", "Compliance Report", "Tax Report",
        "Logistics Report", "Contract Proposal", "Employee Handbook", "Employee Onboarding", "Training Materials",
        "Sales Proposal", "Marketing Plan", "Client Brief", "Service Level Agreement (SLA)", "Product Specification",
        "Performance Review", "Meeting Agenda", "Product Roadmap", "Change Request", "Job Application",
        "Exit Interview", "Workplace Safety Plan", "Employee Evaluation", "Supplier Agreement", "Project Budget",
        "Supplier Invoice", "Asset Management", "Health & Safety Report", "Vendor Contract", "Technical Documentation",
        "Patent Application", "Purchase Requisition", "Event Proposal", "Business Continuity Plan", "Strategic Plan",
        "Legal Brief", "Customer Agreement", "Travel Request", "Expense Report", "Software Release Notes",
        "Audit Trail", "Project Milestones", "Service Report", "IT Incident Report", "Support Ticket",
        "Client Feedback", "Team Meeting Notes", "Employee Benefits Guide", "Operational Plan",
        "Board Meeting Minutes", "Company Newsletter", "Product Review", "Service Agreement", "Customer Service Log",
        "Communication Plan", "Leadership Brief", "Marketing Report", "Team Performance Report",
        "Crisis Management Plan"]

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


def summarize_text(text):
    summarizer = pipeline("summarization")  # Chargement du modèle de résumé
    summary = summarizer(text, max_length=130, min_length=30,
                         do_sample=False)  # Ajustez les paramètres selon vos besoins
    return summary[0]['summary_text']


model = PPO.load("document/rl_model/rl_model/saved_model_v2.zip")


def predict_manager(category):
    User = get_user_model()
    Manager = User.objects.filter(role="manager")
    # Convertir la catégorie en valeur d'état (0 pour "day-off", 1 pour "contract", 2 pour "invoice")
    if category == "day-off":
        state = 0
    elif category == "report":
        state = 1
    elif category == "invoice":
        state = 2
    else:
        raise ValueError(f"Catégorie inconnue: {category}")

    # Utiliser le modèle pour prédire l'action (le manager à choisir)
    action, _states = model.predict(np.array([state]))  # Nous passons l'état à l'algorithme RL

    # Retourner le manager en fonction de l'action choisie
    if action == 0:
        manager = Manager.filter(manager_type="hr").first()  # Si l'action est 0, choisir un manager RH pour "day-off"
    elif action == 1:
        manager = Manager.filter(
            manager_type="reporting").first()  # Si l'action est 1, choisir un manager Comptabilité pour "contract"
    elif action == 2:
        manager = Manager.filter(
            manager_type="finance").first()  # Si l'action est 2, choisir un manager Finance pour "invoice"
    else:
        raise ValueError(f"Action inconnue: {action}")

    return manager


def get_manager_by_gemini(category):
    # Configure the Gemini API with the key from the settings
    genai.configure(api_key=config('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Retrieve all users with the role of manager
    User = get_user_model()
    managers = User.objects.filter(role="manager")

    # Create a list of manager ids and types
    user_lines = ""
    for user in managers:
        user_lines += f"manager_id: {user.id}, manager_type: {user.manager_type}\n"

    # Create a prompt for the Gemini model, including both ID and manager type
    prompt = (
        f"Given the following managers and their types: "
        f"{user_lines}, "
        f"choose the most suitable manager for the category '{category}'. "
        f"Return the ID of the chosen manager."
        "IMPORTANT: ONLY GIVE THE ID OF THE MANAGER, DO NOT SAY ANYTHING ELSE."
    )
    print(prompt)

    # Use Gemini to generate the response
    response = model.generate_content(prompt)

    chosen_manager_id = response.candidates[0].content.parts[0].text
    print(f"Chosen manager ID: {chosen_manager_id}")

    # Find the manager by ID in the database

    # If a valid manager is chosen, return the manager object
    if chosen_manager_id:
        return chosen_manager_id
    else:
        # Return a default manager if no match is found
        return managers.first().id
