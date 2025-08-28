
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RobloxClient:
    def __init__(self):
        self.cookie = os.getenv('ROBLOX_COOKIE')
        if not self.cookie:
            raise ValueError("ROBLOX_COOKIE is not defined in .env file")
        
        self.session = requests.Session()
        self.session.cookies.set('.ROBLOSECURITY', self.cookie)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_user_info(self):
        """Get authenticated user information"""
        try:
            response = self.session.get('https://users.roblox.com/v1/users/authenticated')
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting user info: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_user_id_by_username(self, username):
        """Get user ID by username"""
        try:
            response = requests.post(
                'https://users.roblox.com/v1/usernames/users',
                json={'usernames': [username]},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]['id']
            return None
        except Exception as e:
            print(f"Error searching user: {e}")
            return None
    
    def get_user_experiences(self, user_id):
        """Get all experiences created by a user"""
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
                    try:
                        data = response.json()
                    except ValueError:
                        print("Error: Invalid API response (not JSON)")
                        break
                    
                    # Check if data exists and contains data
                    if data and isinstance(data, dict):
                        if data.get('data') and isinstance(data['data'], list):
                            experiences.extend(data['data'])
                        
                        # Check if there are more pages
                        if data.get('nextPageCursor'):
                            cursor = data['nextPageCursor']
                        else:
                            break
                    else:
                        print("Unexpected data structure from API")
                        break
                        
                elif response.status_code == 401:
                    print("Authentication error - Invalid or expired cookie")
                    break
                elif response.status_code == 403:
                    print("Access denied - Insufficient permissions")
                    break
                else:
                    print(f"API Error: {response.status_code} - {response.text[:100]}")
                    break
            
            return experiences
        except Exception as e:
            print(f"Error getting experiences: {e}")
            return []
    
    def get_robux_balance(self):
        """Get Robux balance"""
        try:
            user_info = self.get_user_info()
            if user_info and 'id' in user_info:
                user_id = user_info['id']
                response = self.session.get(f'https://economy.roblox.com/v1/users/{user_id}/currency')
                if response.status_code == 200:
                    return response.json().get('robux', 0)
            return None
        except Exception as e:
            print(f"Error getting balance: {e}")
            return None
    
    def get_friends_count(self):
        """Get friends count"""
        try:
            user_info = self.get_user_info()
            if user_info and 'id' in user_info:
                user_id = user_info['id']
                response = self.session.get(f'https://friends.roblox.com/v1/users/{user_id}/friends/count')
                if response.status_code == 200:
                    return response.json().get('count', 0)
            return None
        except Exception as e:
            print(f"Error getting friends count: {e}")
            return None

def main():
    try:
        # Create Roblox client instance
        client = RobloxClient()
        
        # Get user information
        user_info = client.get_user_info()
        
        if user_info:
            print("✅ Connected to Roblox!")
            print(f"👤 Username: {user_info.get('name', 'Unknown')}")
            
            # Get Robux balance
            robux = client.get_robux_balance()
            if robux is not None:
                print(f"💰 Robux Balance: {robux}")
                
        else:
            print("❌ Connection failed. Check your Roblox cookie.")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("📝 Make sure to set ROBLOX_COOKIE in your .env file")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
