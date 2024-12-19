import gym
from gym import spaces
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv


# Création d'un environnement personnalisé pour l'entraînement
class ManagerEnv(gym.Env):
    def __init__(self):
        super(ManagerEnv, self).__init__()

        # Définir l'espace d'action : 3 actions possibles (RH, Comptabilité, Finance)
        self.action_space = spaces.Discrete(3)  # RH (0), Comptabilité (1), Finance (2)

        # Catégories disponibles
        self.categories = [
            "day-off", "report", "invoice",  "Documentation", "Design", "Proposal", "Memo", "Agreement", "Receipt", "Letter",
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

        # Définir l'espace d'observation en fonction du nombre de catégories
        self.observation_space = spaces.Discrete(len(self.categories))

    def reset(self):
        """Réinitialise l'environnement à un état aléatoire."""
        self.state = np.random.choice(len(self.categories))  # État aléatoire basé sur les catégories
        return self.state  # Renvoie l'état initial (catégorie du document)

    def step(self, action):
        """Effectuer une étape de l'environnement avec une action donnée."""
        reward = 0

        # Récompenses pour chaque catégorie
        if self.state in [0, 3, 6] and action == 0:  # RH
            reward = 1
        elif self.state in [1, 4, 7] and action == 1:  # Comptabilité
            reward = 1
        elif self.state in [2, 5, 8, 9] and action == 2:  # Finance
            reward = 1
        else:
            reward = -1  # Pénalité pour une action incorrecte

        done = True  # L'épisode se termine après chaque action dans cet environnement simplifié
        info = {}  # Informations supplémentaires (non utilisées ici)

        return self.state, reward, done, info


# Création de l'environnement d'entraînement
env = DummyVecEnv([lambda: ManagerEnv()])

# Initialisation du modèle PPO
model = PPO("MlpPolicy", env, verbose=1)

# Entraînement du modèle
model.learn(total_timesteps=30000)  # Étendre l'entraînement pour les nouvelles catégories

# Sauvegarde du modèle entraîné
model.save("rl_model/saved_model_v2.zip")

print("Entraînement terminé et modèle sauvegardé.")
