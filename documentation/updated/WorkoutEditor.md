# WorkoutEditor Component

The `WorkoutEditor` component is used to create and edit workout templates. It provides a two-panel layout with a workout canvas on the left and an exercise library on the right. Users can drag exercises from the library to the canvas and configure them with sets, reps, RPE/RIR, and notes.

## State

| State | Type | Description |
| --- | --- | --- |
| `clients` | `array` | A list of the trainer's clients. |
| `exerciseData` | `object` | An object containing the exercises, categories, muscles, and equipment from the WGER API. |
| `workoutName` | `string` | The name of the workout template. |
| `workoutDescription` | `string` | The description of the workout template. |
| `configuredExercises` | `array` | A list of the exercises that have been added to the workout template. |
| `loading` | `bool` | A boolean value that indicates whether the component is loading. |
| `syncing` | `bool` | A boolean value that indicates whether the component is syncing with the WGER API. |
| `searchTerm` | `string` | The search term for filtering the exercise library. |
| `selectedCategory` | `string` | The ID of the selected exercise category. |
| `selectedMuscle` | `string` | The ID of the selected muscle. |
| `selectedEquipment` | `string` | The ID of the selected equipment. |
| `showExerciseModal` | `bool` | A boolean value that indicates whether the exercise details modal is visible. |
| `selectedExerciseDetail` | `object` | The exercise that is currently selected in the exercise details modal. |
| `alert` | `object` | An object containing the message and variant for the alert. |

## Functions

| Function | Description |
| --- | --- |
| `fetchData` | Fetches the clients and exercises from the API. |
| `syncWgerExercises` | Syncs the exercises from the WGER API. |
| `showAlert` | Shows an alert message. |
| `handleAddExercise` | Adds an exercise to the workout template. |
| `handleRemoveExercise` | Removes an exercise from the workout template. |
| `handleExerciseConfigChange` | Updates the configuration of an exercise in the workout template. |
| `showExerciseDetails` | Shows the exercise details modal. |
| `handleSaveTemplate` | Saves the workout template. |
| `handleDragEnd` | Handles the drag-and-drop functionality. |

## Usage

```jsx
import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Modal, Spinner } from 'react-bootstrap';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { v4 as uuidv4 } from 'uuid';
import { Search, Filter, Play, Info, People, Calendar, Plus, ArrowRepeat } from 'react-bootstrap-icons';

const WorkoutEditor = () => {
  // ...
};

export default WorkoutEditor;
```
