
import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class GamePassLink:
    def __init__(self):
        self.cookie = os.getenv('ROBLOX_COOKIE')
        if not self.cookie:
            raise ValueError("ROBLOX_COOKIE n'est pas défini dans le fichier .env")
        
        self.session = requests.Session()
        self.session.cookies.set('.ROBLOSECURITY', self.cookie)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_user_experiences(self, user_id):
        """Récupère les expériences d'un utilisateur"""
        try:
            experiences = []
            cursor = ""
            
            while True:
                url = f'https://games.roblox.com/v2/users/{user_id}/games'
                params = {
                    'accessFilter': 'Public',
                    'sortOrder': 'Asc',
                    'limit': 50
                }
                
                if cursor:
                    params['cursor'] = cursor
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        experiences.extend(data['data'])
                    
                    if data.get('nextPageCursor'):
                        cursor = data['nextPageCursor']
                    else:
                        break
                else:
                    print(f"Erreur API: {response.status_code}")
                    break
            
            return experiences
        except Exception as e:
            print(f"Erreur lors de la récupération des expériences: {e}")
            return []
    
    def create_gamepass_link(self, experience_id):
        """Crée le lien pour créer un GamePass"""
        return f"https://create.roblox.com/dashboard/creations/experiences/{experience_id}/monetization/passes"
    
    def get_game_passes(self, experience_id):
        """Récupère tous les GamePass d'une expérience"""
        try:
            url = f'https://games.roblox.com/v1/games/{experience_id}/game-passes'
            params = {
                'limit': 100,
                'sortOrder': 'Desc'
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                print(f"Erreur API GamePass: {response.status_code}")
                return []
        except Exception as e:
            print(f"Erreur lors de la récupération des GamePass: {e}")
            return []
    
    def get_game_pass_details(self, gamepass_id):
        """Récupère les détails d'un GamePass spécifique"""
        try:
            url = f'https://games.roblox.com/v1/game-passes/{gamepass_id}'
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur API GamePass details: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération des détails GamePass: {e}")
            return None
