# Exercise Library Schema

This document defines the JSON structure for the `exercises.json` database file, enhanced with WGER API integration.

## Exercise Object Structure

Each exercise in the library will be represented as a JSON object with the following fields:

| Field              | Type     | Description                                                                                             | Example                               |
|-------------------|----------|---------------------------------------------------------------------------------------------------------|---------------------------------------|
| `id`              | String   | A unique identifier for the exercise in our system. UUID or nanoid.                                     | `"exr_123abc"`                        |
| `wger_id`         | Integer  | WGER exercise ID for API reference (optional, null for custom exercises)                               | `73`                                  |
| `wger_uuid`       | String   | WGER exercise UUID for API reference (optional, null for custom exercises)                             | `"3717d144-7815-4a97-9a56-956fb889c996"` |
| `name`            | String   | The name of the exercise.                                                                               | `"Barbell Bench Press"`               |
| `instructions`    | String   | Step-by-step instructions on how to perform the exercise correctly.                                     | `"1. Lie flat on the bench...\n2. ..."` |
| `description`     | String   | Detailed description of the exercise (from WGER exerciseinfo)                                          | `"The bench press is a compound..."`  |
| `mediaUrl`        | String   | Primary URL pointing to a video (e.g., YouTube) or main demonstration image                            | `"https://youtube.com/watch?v=..."`   |
| `category`        | Object   | Exercise category information                                                                           | `{"id": 11, "name": "Chest"}`        |
| `muscles`         | Array    | Primary muscles worked                                                                                  | `[{"id": 4, "name": "Pectoralis major", "name_en": "Chest"}]` |
| `muscles_secondary` | Array  | Secondary muscles worked                                                                                | `[{"id": 2, "name": "Anterior deltoid", "name_en": "Shoulders"}]` |
| `equipment`       | Array    | Required equipment                                                                                      | `[{"id": 1, "name": "Barbell"}]`     |
| `images`          | Array    | Array of demonstration images                                                                           | `[{"url": "...", "is_main": true}]`  |
| `videos`          | Array    | Array of demonstration videos                                                                           | `[{"url": "...", "platform": "youtube"}]` |
| `difficulty`      | String   | Exercise difficulty level                                                                               | `"intermediate"`                      |
| `license_author`  | String   | Attribution for exercise content (from WGER)                                                           | `"Everkinetic"`                       |
| `created_at`      | String   | ISO timestamp when exercise was added to our system                                                    | `"2024-01-15T10:30:00Z"`             |
| `updated_at`      | String   | ISO timestamp when exercise was last updated                                                           | `"2024-01-15T10:30:00Z"`             |
| `is_custom`       | Boolean  | Whether this is a custom exercise (not from WGER)                                                      | `false`                               |

## Category Object Structure

```json
{
  "id": 11,
  "name": "Chest",
  "wger_id": 11
}
```

## Muscle Object Structure

```json
{
  "id": 4,
  "name": "Pectoralis major",
  "name_en": "Chest",
  "is_front": true,
  "image_url_main": "/static/images/muscles/main/muscle-4.svg",
  "image_url_secondary": "/static/images/muscles/secondary/muscle-4.svg",
  "wger_id": 4
}
```

## Equipment Object Structure

```json
{
  "id": 1,
  "name": "Barbell",
  "wger_id": 1
}
```

## Image Object Structure

```json
{
  "id": "img_123",
  "url": "https://wger.de/media/exercise-images/192/Bench-press-1.png",
  "is_main": true,
  "license_author": "Everkinetic",
  "wger_id": 68
}
```

## Video Object Structure

```json
{
  "id": "vid_123",
  "url": "https://youtube.com/watch?v=...",
  "platform": "youtube",
  "title": "Bench Press Technique",
  "wger_id": 15
}
```

## Example Enhanced `exercises.json`

```json
{
  "exercises": [
    {
      "id": "exr_a1b2c3d4",
      "wger_id": 73,
      "wger_uuid": "3717d144-7815-4a97-9a56-956fb889c996",
      "name": "Bench Press",
      "instructions": "Lie on a flat bench, grip the barbell with hands slightly wider than shoulder-width apart. Lower the bar to your chest, then press it back up to the starting position.",
      "description": "The bench press is a compound exercise that primarily targets the pectoralis major, anterior deltoids, and triceps. It's one of the fundamental movements in strength training.",
      "mediaUrl": "https://wger.de/media/exercise-images/192/Bench-press-1.png",
      "category": {
        "id": 11,
        "name": "Chest",
        "wger_id": 11
      },
      "muscles": [
    {
          "id": 4,
          "name": "Pectoralis major",
          "name_en": "Chest",
          "is_front": true,
          "image_url_main": "/static/images/muscles/main/muscle-4.svg",
          "image_url_secondary": "/static/images/muscles/secondary/muscle-4.svg",
          "wger_id": 4
        }
      ],
      "muscles_secondary": [
        {
          "id": 2,
          "name": "Anterior deltoid",
          "name_en": "Shoulders",
          "is_front": true,
          "image_url_main": "/static/images/muscles/main/muscle-2.svg",
          "image_url_secondary": "/static/images/muscles/secondary/muscle-2.svg",
          "wger_id": 2
        },
        {
          "id": 5,
          "name": "Triceps brachii",
          "name_en": "Triceps",
          "is_front": false,
          "image_url_main": "/static/images/muscles/main/muscle-5.svg",
          "image_url_secondary": "/static/images/muscles/secondary/muscle-5.svg",
          "wger_id": 5
        }
      ],
      "equipment": [
        {
          "id": 1,
          "name": "Barbell",
          "wger_id": 1
        },
        {
          "id": 8,
          "name": "Bench",
          "wger_id": 8
        }
      ],
      "images": [
        {
          "id": "img_68",
          "url": "https://wger.de/media/exercise-images/192/Bench-press-1.png",
          "is_main": true,
          "license_author": "Everkinetic",
          "wger_id": 68
        }
      ],
      "videos": [],
      "difficulty": "intermediate",
      "license_author": "sistab2",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "is_custom": false
    },
    {
      "id": "exr_custom_001",
      "wger_id": null,
      "wger_uuid": null,
      "name": "Custom Exercise",
      "instructions": "Custom exercise instructions...",
      "description": "A custom exercise created by the trainer.",
      "mediaUrl": "https://youtube.com/watch?v=custom",
      "category": {
        "id": 11,
        "name": "Chest",
        "wger_id": null
      },
      "muscles": [],
      "muscles_secondary": [],
      "equipment": [],
      "images": [],
      "videos": [],
      "difficulty": "beginner",
      "license_author": null,
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "is_custom": true
    }
  ],
  "categories": [
    {
      "id": 10,
      "name": "Abs",
      "wger_id": 10
    },
    {
      "id": 8,
      "name": "Arms",
      "wger_id": 8
    },
    {
      "id": 12,
      "name": "Back",
      "wger_id": 12
    },
    {
      "id": 14,
      "name": "Calves",
      "wger_id": 14
    },
    {
      "id": 15,
      "name": "Cardio",
      "wger_id": 15
    },
    {
      "id": 11,
      "name": "Chest",
      "wger_id": 11
    },
    {
      "id": 9,
      "name": "Legs",
      "wger_id": 9
    },
    {
      "id": 13,
      "name": "Shoulders",
      "wger_id": 13
    }
  ],
  "muscles": [
    {
      "id": 2,
      "name": "Anterior deltoid",
      "name_en": "Shoulders",
      "is_front": true,
      "image_url_main": "https://wger.de/static/images/muscles/main/muscle-2.svg",
      "image_url_secondary": "https://wger.de/static/images/muscles/secondary/muscle-2.svg",
      "wger_id": 2
    }
  ],
  "equipment": [
    {
      "id": 1,
      "name": "Barbell",
      "wger_id": 1
    }
  ],
  "sync_info": {
    "last_sync": "2024-01-15T10:30:00Z",
    "wger_api_version": "v2",
    "total_exercises": 662,
    "synced_exercises": 100
  }
}
```

## Migration Notes

When migrating from the old schema to the new enhanced schema:

1. Existing exercises will have `wger_id` and `wger_uuid` set to `null`
2. `is_custom` will be set to `true` for existing exercises
3. New fields will be populated with default values or empty arrays
4. WGER-sourced exercises will have complete metadata

## API Integration Notes

- Use `wger_id` and `wger_uuid` for API synchronization
- Respect `license_author` for attribution requirements
- Update `updated_at` timestamp when syncing from WGER
- Maintain both custom and WGER exercises in the same structure