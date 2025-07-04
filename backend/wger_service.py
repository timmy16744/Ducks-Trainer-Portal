import requests
import json
import os
from datetime import datetime, timezone
import time
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WgerService:
    """Service class for integrating with WGER API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://wger.de/api/v2"
        self.headers = {
            'Authorization': f'Token {api_key}',
            'User-Agent': 'DucksTrainerPortal/1.0'
        }
        self.database_path = "database"
        self.exercises_file = os.path.join(self.database_path, "exercises.json")
        
        # Create database directory if it doesn't exist
        os.makedirs(self.database_path, exist_ok=True)
        
        # Initialize exercises file if it doesn't exist
        if not os.path.exists(self.exercises_file):
            self._initialize_exercises_file()
    
    def _initialize_exercises_file(self):
        """Initialize the exercises.json file with empty structure"""
        initial_data = {
            "exercises": [],
            "categories": [],
            "muscles": [],
            "equipment": [],
            "sync_info": {
                "last_sync": None,
                "wger_api_version": "v2",
                "total_exercises": 0,
                "synced_exercises": 0
            }
        }
        with open(self.exercises_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to WGER API with error handling and rate limiting"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # Rate limiting - be respectful to the API
            time.sleep(0.1)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None
    
    def _get_paginated_data(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Fetch all paginated data from an endpoint"""
        all_data = []
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if params is None:
            params = {}

        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params if not all_data else None)
                response.raise_for_status()
                data = response.json()
                
                all_data.extend(data.get('results', []))
                url = data.get('next')
                
                logger.info(f"Fetched {len(all_data)} items from {endpoint}")
                time.sleep(0.1) # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for {url}: {e}")
                break
                
        return all_data
    
    def fetch_categories(self) -> List[Dict]:
        """Fetch exercise categories from WGER"""
        logger.info("Fetching exercise categories...")
        categories = self._get_paginated_data("exercisecategory/")
        
        # Transform to our schema
        transformed_categories = []
        for cat in categories:
            transformed_categories.append({
                "id": cat["id"],
                "name": cat["name"],
                "wger_id": cat["id"]
            })
        
        return transformed_categories
    
    def fetch_muscles(self) -> List[Dict]:
        """Fetch muscles from WGER"""
        logger.info("Fetching muscles...")
        muscles = self._get_paginated_data("muscle/")
        
        # Transform to our schema
        transformed_muscles = []
        for muscle in muscles:
            transformed_muscles.append({
                "id": muscle["id"],
                "name": muscle["name"],
                "name_en": muscle.get("name_en", muscle["name"]),
                "is_front": muscle["is_front"],
                "image_url_main": f"https://wger.de{muscle['image_url_main']}",
                "image_url_secondary": f"https://wger.de{muscle['image_url_secondary']}",
                "wger_id": muscle["id"]
            })
        
        return transformed_muscles
    
    def fetch_equipment(self) -> List[Dict]:
        """Fetch equipment from WGER"""
        logger.info("Fetching equipment...")
        equipment = self._get_paginated_data("equipment/")
        
        # Transform to our schema
        transformed_equipment = []
        for eq in equipment:
            transformed_equipment.append({
                "id": eq["id"],
                "name": eq["name"],
                "wger_id": eq["id"]
            })
        
        return transformed_equipment
    
    def fetch_exercises(self, limit: int = 100) -> List[Dict]:
        """Fetch exercises from WGER with English language filter and all related data."""
        logger.info(f"Fetching up to {limit} exercises using the recommended 'exerciseinfo' endpoint...")

        # Use the /exerciseinfo/ endpoint as it provides all nested data
        exercises_info = self._get_paginated_data("exerciseinfo/", {"language": 2, "limit": limit})
        
        if not exercises_info:
            logger.error("Failed to fetch exercises from /exerciseinfo/")
            return []

        transformed_exercises = []
        for info in exercises_info:
            # Find the English translation for name and description
            english_translation = next((t for t in info.get("translations", []) if t.get("language") == 2), None)

            name = english_translation["name"] if english_translation and english_translation.get("name") else f"Exercise {info['id']}"
            description = english_translation["description"] if english_translation and english_translation.get("description") else "No description available."

            media_url = ""
            if info.get("images"):
                main_image = next((img for img in info["images"] if img.get("is_main")), info["images"][0])
                media_url = main_image.get("image", "")

            transformed_exercise = {
                "id": f"exr_wger_{info['id']}",
                "wger_id": info['id'],
                "wger_uuid": info.get("uuid", ""),
                "name": name,
                "instructions": description,
                "description": description,
                "mediaUrl": media_url,
                "category": info.get("category"),
                "muscles": info.get("muscles", []),
                "muscles_secondary": info.get("muscles_secondary", []),
                "equipment": info.get("equipment", []),
                "images": info.get("images", []),
                "videos": info.get("videos", []),
                "difficulty": "intermediate", # This can be enhanced if the API provides it
                "license_author": info.get("license_author", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "is_custom": False
            }
            transformed_exercises.append(transformed_exercise)

        logger.info(f"Successfully transformed {len(transformed_exercises)} exercises")
        return transformed_exercises
    
    def sync_exercises(self, limit: int = 100) -> Dict[str, Any]:
        """Sync exercises from WGER and update local database"""
        logger.info("Starting WGER sync...")
        
        try:
            with open(self.exercises_file, 'r') as f:
                existing_data = json.load(f)
            
            custom_exercises = [ex for ex in existing_data.get("exercises", []) if ex.get("is_custom")]
            
            new_exercises = self.fetch_exercises(limit)
            
            # We need to fetch these separately to have them available for the UI, even if no exercises use them
            new_categories = self.fetch_categories()
            new_muscles = self.fetch_muscles()
            new_equipment = self.fetch_equipment()

            all_exercises = custom_exercises + new_exercises
            
            updated_data = {
                "exercises": all_exercises,
                "categories": new_categories,
                "muscles": new_muscles,
                "equipment": new_equipment,
                "sync_info": {
                    "last_sync": datetime.now(timezone.utc).isoformat(),
                    "wger_api_version": "v2",
                    "total_exercises": len(all_exercises),
                    "synced_exercises": len(new_exercises)
                }
            }
            
            with open(self.exercises_file, 'w') as f:
                json.dump(updated_data, f, indent=2)
            
            sync_result = {
                "status": "success",
                "synced_exercises": len(new_exercises),
                "total_exercises": len(all_exercises),
                "custom_exercises": len(custom_exercises),
                "sync_time": updated_data["sync_info"]["last_sync"]
            }
            
            logger.info(f"Sync completed successfully: {sync_result}")
            return sync_result
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sync_time": datetime.now(timezone.utc).isoformat()
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        try:
            with open(self.exercises_file, 'r') as f:
                data = json.load(f)
            return data.get("sync_info", {})
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {"status": "error", "error": str(e)}

# Example usage
if __name__ == "__main__":
    # Test the service with your API key
    API_KEY = "397683a6bb806f7e4c2d1c0b5a210a8a3f07b442"
    
    wger_service = WgerService(API_KEY)
    result = wger_service.sync_exercises(limit=50)  # Start with 50 exercises for testing
    print(json.dumps(result, indent=2)) 