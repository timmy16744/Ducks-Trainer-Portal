# Program Module Schema

This document outlines the data structures for the enhanced workout program module.

## 1. `workout_templates.json`

Stores the master copies of multi-day workout programs created by the trainer. These are the templates from which client-specific programs are generated.

**Structure:**
- Array of `ProgramTemplate` objects.

**`ProgramTemplate` Object:**
```json
{
  "id": "prog_template_ppl_01",
  "name": "Push Pull Legs Split",
  "description": "A classic 3-day PPL split for strength and hypertrophy.",
  "tags": ["strength", "ppl", "intermediate"],
  "days": [
    {
      "day": 1,
      "name": "Push Day",
      "description": "Focus on chest, shoulders, and triceps.",
      "groups": [
        {
          "id": "group_1",
          "type": "standard",
          "exercises": [
            {
              "exercise_id": "exr_wger_801",
              "sets": "3",
              "reps": "8-12",
              "rpe": "8",
              "rest": "60"
            }
          ]
        },
        {
          "id": "group_2",
          "type": "superset",
          "exercises": [
            {
              "exercise_id": "exr_wger_20",
              "sets": "3",
              "reps": "10-15",
              "rpe": "9",
              "rest": "0"
            },
            {
              "exercise_id": "exr_wger_805",
              "sets": "3",
              "reps": "10-15",
              "rpe": "9",
              "rest": "90"
            }
          ]
        }
      ]
    }
  ]
}
```

## 2. `client_workouts.json`

Stores the assigned, editable copies of workout programs for each client. When a trainer assigns a program, a copy of the template is created here and linked to the client.

**Structure:**
- Array of `ClientProgram` objects.

**`ClientProgram` Object:**
```json
{
  "id": "client_prog_12345",
  "client_id": "client_abc",
  "template_id": "prog_template_ppl_01",
  "name": "Push Pull Legs Split",
  "description": "A classic 3-day PPL split, modified for Tim's shoulder.",
  "start_date": "2025-07-08",
  "days": [
  ]
}
```

## 3. `workout_logs.json`

A chronological record of every workout a client completes. This is the source of truth for exercise history and for pre-populating future sessions.

**Structure:**
- Array of `WorkoutLog` objects.

**`WorkoutLog` Object:**
```json
{
  "log_id": "log_abcdef",
  "client_id": "client_abc",
  "client_program_id": "client_prog_12345",
  "day_index": 1,
  "date_completed": "2025-07-09T18:30:00Z",
  "notes": "Felt strong on bench today.",
  "logged_exercises": [
    {
      "exercise_id": "exr_wger_801",
      "sets": [
        { "set": 1, "reps": 12, "weight": 50, "rpe": 7 },
        { "set": 2, "reps": 11, "weight": 50, "rpe": 8 },
        { "set": 3, "reps": 10, "weight": 50, "rpe": 8 }
      ]
    }
  ]
}
```
