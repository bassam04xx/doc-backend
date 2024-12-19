import os
import sys
import django
import numpy as np
from django.contrib.auth import get_user_model
from stable_baselines3 import PPO

# Add the project directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")  # Replace 'doc_backend.settings' with your actual settings module

# Configure Django
django.setup()

# Import the model after setting up Django
User = get_user_model()
Manager = User.objects.filter(role="manager")

# Load the pre-trained model
model = PPO.load("rl_model/saved_model.zip")

# Function to predict the manager based on the document category
def predict_manager(category):
    if category == "day-off":
        state = 0
    elif category == "report":
        state = 1
    elif category == "invoice":
        state = 2
    else:
        raise ValueError(f"Unknown category: {category}")

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
    category = "invoice"
    manager = predict_manager(category)
    print(f"Selected manager: {manager.username}")
