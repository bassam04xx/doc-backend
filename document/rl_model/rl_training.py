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

        # Définir l'espace d'observation : 3 catégories possibles (day-off, contract, invoice)
        self.observation_space = spaces.Discrete(3)  # 0 -> "day-off", 1 -> "contract", 2 -> "invoice"

        # Catégories disponibles
        self.categories = ["day-off", "contract", "invoice"]

    def reset(self):
        """Réinitialise l'environnement à un état aléatoire."""
        self.state = np.random.choice([0, 1, 2])  # 0 -> "day-off", 1 -> "contract", 2 -> "invoice"
        return self.state  # Renvoie l'état initial (catégorie du document)

    def step(self, action):
        """Effectuer une étape de l'environnement avec une action donnée."""
        # On attribue une récompense en fonction de l'action et de la catégorie
        reward = 0

        if self.state == 0:  # Si la catégorie est "day-off"
            if action == 0:  # Si l'action est RH
                reward = 1  # Récompense si l'action correspond à "day-off"
            else:
                reward = -1  # Pénalité pour toute autre action
        elif self.state == 1:  # Si la catégorie est "contract"
            if action == 1:  # Si l'action est Comptabilité
                reward = 1  # Récompense si l'action correspond à "contract"
            else:
                reward = -1  # Pénalité pour toute autre action
        elif self.state == 2:  # Si la catégorie est "invoice"
            if action == 2:  # Si l'action est Finance
                reward = 1  # Récompense si l'action correspond à "invoice"
            else:
                reward = -1  # Pénalité pour toute autre action

        done = True  # L'épisode se termine après chaque action dans cet environnement simplifié
        info = {}  # Information supplémentaire (non utilisé ici)

        return self.state, reward, done, info


# Création de l'environnement d'entraînement
env = DummyVecEnv([lambda: ManagerEnv()])

# Initialisation du modèle PPO
model = PPO("MlpPolicy", env, verbose=1)

# Entraînement du modèle
model.learn(total_timesteps=20000)

# Sauvegarde du modèle entraîné
model.save("rl_model/saved_model.zip")

print("Entraînement terminé et modèle sauvegardé.")
