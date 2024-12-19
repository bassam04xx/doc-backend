import os
import sys
import django
import numpy as np
from django.contrib.auth import get_user_model
from stable_baselines3 import PPO

# Add the project directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")  # Replace 'project.settings' with your actual settings module

# Configure Django
django.setup()

# Import the model after setting up Django
User = get_user_model()
Manager = User.objects.filter(role="manager")

# Load the pre-trained model
model = PPO.load("rl_model/saved_model_v2.zip")

# Expanded categories map to match the training environment
categories_map = {
    "day-off": 0, "report": 1, "invoice": 2, "Documentation": 3, "Design": 4, "Proposal": 5,
    "Memo": 6, "Agreement": 7, "Receipt": 8, "Letter": 9, "Manual": 10, "Presentation": 11,
    "Email": 12, "Resume": 13, "Minutes": 14, "Checklist": 15, "Policy": 16, "Procedure": 17,
    "Research Paper": 18, "Whitepaper": 19, "Guideline": 20, "Testimonial": 21, "Certificate": 22,
    "Order": 23, "SOW (Statement of Work)": 24, "Project Plan": 25, "Budget": 26,
    "Financial Statement": 27, "Contract Amendment": 28, "Project Update": 29, "Job Description": 30,
    "Non-disclosure Agreement (NDA)": 31, "Tender": 32, "Legal Notice": 33, "Patent": 34,
    "Press Release": 35, "Event Flyer": 36, "Newsletter": 37, "Statement": 38, "Application Form": 39,
    "Transcript": 40, "Report Summary": 41, "Project Charter": 42, "Presentation Slides": 43,
    "Terms and Conditions": 44, "Agreement Addendum": 45, "Purchase Order": 46,
    "Order Confirmation": 47, "Business Letter": 48, "Letter of Intent": 49, "Internal Memo": 50,
    "Customer Feedback": 51, "Work Order": 52, "Audit Report": 53, "Risk Assessment": 54,
    "Compliance Report": 55, "Tax Report": 56, "Logistics Report": 57, "Contract Proposal": 58,
    "Employee Handbook": 59, "Employee Onboarding": 60, "Training Materials": 61, "Sales Proposal": 62,
    "Marketing Plan": 63, "Client Brief": 64, "Service Level Agreement (SLA)": 65,
    "Product Specification": 66, "Performance Review": 67, "Meeting Agenda": 68, "Product Roadmap": 69,
    "Change Request": 70, "Job Application": 71, "Exit Interview": 72, "Workplace Safety Plan": 73,
    "Employee Evaluation": 74, "Supplier Agreement": 75, "Project Budget": 76,
    "Supplier Invoice": 77, "Asset Management": 78, "Health & Safety Report": 79, "Vendor Contract": 80,
    "Technical Documentation": 81, "Patent Application": 82, "Purchase Requisition": 83,
    "Event Proposal": 84, "Business Continuity Plan": 85, "Strategic Plan": 86, "Legal Brief": 87,
    "Customer Agreement": 88, "Travel Request": 89, "Expense Report": 90, "Software Release Notes": 91,
    "Audit Trail": 92, "Project Milestones": 93, "Service Report": 94, "IT Incident Report": 95,
    "Support Ticket": 96, "Client Feedback": 97, "Team Meeting Notes": 98, "Employee Benefits Guide": 99,
    "Operational Plan": 100, "Board Meeting Minutes": 101, "Company Newsletter": 102,
    "Product Review": 103, "Service Agreement": 104, "Customer Service Log": 105, "Communication Plan": 106,
    "Leadership Brief": 107, "Marketing Report": 108, "Team Performance Report": 109,
    "Crisis Management Plan": 110
}

# Function to predict the manager based on the document category
def predict_manager(category):
    if category not in categories_map:
        raise ValueError(f"Unknown category: {category}")

    state = categories_map[category]
    action, _states = model.predict(np.array([state]))

    if action == 0:
        manager = Manager.filter(manager_type="hr").first()
    elif action == 1:
        manager = Manager.filter(manager_type="reporting").first()
    elif action == 2:
        manager = Manager.filter(manager_type="finance").first()
    else:
        raise ValueError(f"Unknown action: {action}")

    return manager

# Example usage
if __name__ == "__main__":
    category = "Expense Report"  # Example category
    try:
        manager = predict_manager(category)
        print(f"Selected manager: {manager.username if manager else 'No manager found'}")
    except ValueError as e:
        print(e)
