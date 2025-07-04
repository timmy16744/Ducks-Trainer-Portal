# WGER API Integration Documentation

WGER is an open-source fitness platform that provides a comprehensive REST API for accessing exercise data, including exercise descriptions, images, videos, muscle groups, and equipment information.

## API Overview

- **Base URL:** `https://wger.de/api/v2/`
- **Authentication:** API Key based authentication
- **Format:** JSON
- **Rate Limits:** Standard rate limiting applies
- **Language Support:** Multiple languages available (language=2 for English)

## Authentication

WGER uses API key authentication. Include your API key in the request headers:

```
Authorization: Token YOUR_API_KEY
```

## Key Endpoints

### 1. Exercises
- **Endpoint:** `/api/v2/exercise/`
- **Parameters:**
  - `language=2` (English)
  - `limit` (pagination)
  - `offset` (pagination)
- **Returns:** List of exercises with metadata

### 2. Exercise Info (Detailed)
- **Endpoint:** `/api/v2/exerciseinfo/`
- **Returns:** Detailed exercise information including descriptions

### 3. Exercise Images
- **Endpoint:** `/api/v2/exerciseimage/`
- **Parameters:**
  - `exercise_base` (filter by exercise)
- **Returns:** Exercise demonstration images

### 4. Exercise Videos
- **Endpoint:** `/api/v2/video/`
- **Returns:** Exercise demonstration videos

### 5. Muscles
- **Endpoint:** `/api/v2/muscle/`
- **Returns:** Muscle group information with SVG images

### 6. Exercise Categories
- **Endpoint:** `/api/v2/exercisecategory/`
- **Returns:** Exercise categories (Arms, Legs, Chest, etc.)

### 7. Equipment
- **Endpoint:** `/api/v2/equipment/`
- **Returns:** Equipment information

## Data Structures

### Exercise Object
```json
{
  "id": 73,
  "uuid": "3717d144-7815-4a97-9a56-956fb889c996",
  "created": "2023-08-06T10:17:17.422900+02:00",
  "last_update": "2024-01-17T11:23:51.262565+01:00",
  "category": 11,
  "muscles": [4],
  "muscles_secondary": [2, 5],
  "equipment": [1, 8],
  "variations": 7,
  "license_author": "sistab2"
}
```

### Exercise Info Object
```json
{
  "id": 123,
  "exercise": 73,
  "name": "Bench Press",
  "description": "Detailed exercise instructions...",
  "language": 2
}
```

### Exercise Image Object
```json
{
  "id": 68,
  "uuid": "08517378-bc36-4f6b-9952-1f45a02d936e",
  "exercise": 73,
  "exercise_uuid": "3717d144-7815-4a97-9a56-956fb889c996",
  "image": "https://wger.de/media/exercise-images/192/Bench-press-1.png",
  "is_main": true,
  "style": "1",
  "license": 1,
  "license_author": "Everkinetic"
}
```

### Muscle Object
```json
{
  "id": 4,
  "name": "Pectoralis major",
  "name_en": "Chest",
  "is_front": true,
  "image_url_main": "/static/images/muscles/main/muscle-4.svg",
  "image_url_secondary": "/static/images/muscles/secondary/muscle-4.svg"
}
```

## Integration Strategy

### 1. Data Synchronization
- Fetch exercises, muscles, categories, and equipment on app initialization
- Store in local database for offline access
- Implement periodic sync to get updates

### 2. Local Schema Mapping
Map WGER data to our local exercise schema:
- `wger_id`: WGER exercise ID
- `id`: Our local unique ID
- `name`: Exercise name from exerciseinfo
- `instructions`: Description from exerciseinfo
- `mediaUrl`: Primary image or video URL
- `category`: Exercise category
- `muscles`: Primary muscles worked
- `muscles_secondary`: Secondary muscles
- `equipment`: Required equipment
- `images`: Array of demonstration images
- `videos`: Array of demonstration videos

### 3. Caching Strategy
- Cache exercise data locally for 24 hours
- Implement incremental updates using `last_update` timestamps
- Fallback to cached data if API is unavailable

### 4. Error Handling
- Graceful degradation if API is unavailable
- Retry logic for failed requests
- Validation of API response data

## Implementation Notes

1. **Language Selection:** Use `language=2` for English content
2. **Pagination:** API returns paginated results, implement proper pagination handling
3. **Rate Limiting:** Respect API rate limits with appropriate delays
4. **Image Optimization:** Consider caching/resizing images for better performance
5. **Data Validation:** Validate all incoming data before storing locally
6. **Licensing:** Respect exercise licensing information and attribution requirements

## Example Usage

```python
import requests

def fetch_exercises(api_key, language=2, limit=100):
    headers = {'Authorization': f'Token {api_key}'}
    url = f'https://wger.de/api/v2/exercise/?language={language}&limit={limit}'
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'API request failed: {response.status_code}')
```

## Benefits of Integration

1. **Comprehensive Database:** Access to 600+ exercises
2. **Rich Media:** Professional images and videos
3. **Structured Data:** Muscle groups, categories, equipment
4. **Multilingual:** Support for multiple languages
5. **Active Maintenance:** Regularly updated database
6. **Open Source:** Free to use with proper attribution 