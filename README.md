# Ducks Trainer Portal - The Ultimate Self-Hosted Coaching Platform

This repository contains the complete application for the Ducks Trainer Portal, a self-hosted platform for personal trainers to manage clients, design workout programs, and track progress under their own brand.

This project is built with a **React frontend** and a **Flask backend**, using a **SQLite** database for data persistence.

---

## Key Features

- **Client Management**: A full-featured client roster with onboarding, archiving, and detailed profiles. All client information is editable directly within the UI.
- **Dynamic Program Design**:
  - **Exercise Library**: A comprehensive library of exercises, imported locally to ensure reliability.
  - **Workout Editor**: Build custom workout templates with a drag-and-drop interface, supporting sets, reps, notes, and advanced types like supersets.
  - **Program Dashboard**: Assign multi-day workout programs to individual clients or groups.
- **Data-Driven Insights**:
  - **Progress Tracking**: Monitor client body stats, workout logs, and more.
  - **Alerts Dashboard**: Get notifications for important client events.
- **Resource & Communication Hub**:
  - Upload and share resources like PDFs and videos.
  - Integrated chat for real-time communication.
- **100% White-Label**: Your brand, your domain.

---

## Tech Stack

- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: React (Create React App) with Tailwind CSS
- **Real-time Communication**: Flask-SocketIO
- **Database**: SQLite
- **Database Migrations**: Flask-Migrate with Alembic

---

## Local Development Setup

Follow these steps to get the application running on your local machine.

### Prerequisites

- **Python** (3.8+ recommended)
- **Node.js** (LTS version recommended) & **npm**

### 1. Initial Setup (Run Once)

Clone the repository and install all dependencies from the project root directory.

```bash
# Navigate to your project's root folder
# e.g., C:\Users\timhu\Documents\Ducks Trainer Portal

# Install both frontend and backend dependencies
npm install
```
*This command will run `npm install` in the `frontend` directory and `pip install -r requirements.txt` in the `backend` directory.*

### 2. Database Initialization (Run Once)

Before you start the servers for the first time, you need to initialize the database and import the exercise library.

```bash
# From the project root folder:

# 1. Create the initial database schema
npm run db:upgrade

# 2. Import the exercise library from the local JSON file
npm run db:import-exercises
```

### 3. Running the Application

To run the application, you need to start both the backend and frontend servers. It's recommended to do this in two separate terminals.

**Terminal 1: Start the Backend (Flask)**

```bash
# Navigate to the backend directory
cd backend

# Start the Flask server
python run.py
```
The backend will be running at `http://localhost:5000`.

**Terminal 2: Start the Frontend (React)**

```bash
# Navigate to the frontend directory
cd frontend

# Start the React development server
npm start
```
The frontend will open automatically in your browser at `http://localhost:3000`.

---

## Database Migrations Workflow

As you develop the application, you will inevitably need to change the database schema by modifying `backend/models.py`. We have a simple, reliable workflow for this.

After you have changed the `models.py` file, run the following two commands from the **project root directory**:

**1. Create the Migration Script**

This command detects your changes and generates a new migration file.

```bash
# Add a short, descriptive message about the changes
npm run db:migrate -m "Your descriptive message here"
```

**2. Apply the Migration**

This command applies the changes from the new migration file to your database.

```bash
npm run db:upgrade
```

That's it! Your database schema is now up-to-date with your models. There is no need to manually handle environment variables or change directories.
