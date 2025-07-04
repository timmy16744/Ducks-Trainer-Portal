# The Ultimate Self-Hosted Coaching Portal

This repository contains the complete application template for a self-hosted coaching portal, designed for personal trainers to manage clients, track progress, and deliver exceptional value under their own brand.

## Features

- **Client Management:** Add, organize, and manage clients with ease.
- **Workout Builder & Tracking:** Create custom workout plans and enable clients to log their progress.
- **Nutrition Planning & Tracking:** Offer meal plans or allow clients to track their macros.
- **Progress Visualization:** Track body stats, progress photos, and workout metrics with intuitive graphs.
- **Real-time Communication:** Stay connected with your clients through an integrated chat feature.
- **100% White-Label:** Your brand, your domain. No third-party branding.

## Styling

This project uses **Tailwind CSS** for styling. All components are styled using Tailwind's utility classes.

## Deployment to Vercel (One-Click)

This application is designed for one-click deployment to Vercel. Follow these steps:

1.  **Purchase a License Key:** Obtain your unique lifetime license key from [Your Marketing Website Link Here].
2.  **Clone this Repository:** Click the "Use this template" button on GitHub or clone this repository to your local machine.
3.  **Connect to Vercel:**
    -   Log in to your Vercel account (or sign up for free).
    -   Click "Add New..." -> "Project".
    -   Select "Import Git Repository" and choose your cloned repository.
4.  **Configure Environment Variables:**
    -   During the Vercel setup, you will be prompted to configure environment variables. Add the following:
        -   `TRAINER_PASSWORD`: Set this to your desired password for trainer login.
        -   `LICENSE_KEY`: Paste the unique license key you purchased.
5.  **Deploy:** Click "Deploy". Vercel will automatically build and deploy your application.
6.  **Connect Custom Domain (Optional):** After deployment, you can connect your custom domain in your Vercel project settings.

## Local Development

To run the application locally for development or testing:

### Prerequisites

-   Python 3.8+
-   Node.js (LTS recommended)
-   npm or yarn

### Backend Setup (Flask)

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    # On Windows:
    # .venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    (You may need to create a `requirements.txt` file first by running `pip freeze > requirements.txt` after installing Flask, Flask-CORS, Flask-SocketIO, python-socketio, python-engineio, simple-websocket, bidict, wsproto)
4.  Set environment variables (replace with your desired values):
    ```bash
    # On Windows (Command Prompt):
    # set TRAINER_PASSWORD=your_trainer_password
    # set LICENSE_KEY=your_license_key
    # On Windows (PowerShell):
    # $env:TRAINER_PASSWORD="your_trainer_password"
    # $env:LICENSE_KEY="your_license_key"
    # On macOS/Linux:
    # export TRAINER_PASSWORD=your_trainer_password
    # export LICENSE_KEY=your_license_key
    ```
5.  Run the Flask backend:
    ```bash
    python app.py
    ```

### Frontend Setup (React)

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    # or yarn install
    ```
3.  Start the React development server:
    ```bash
    npm start
    # or yarn start
    ```

Your application should now be running locally. The backend will be on `http://localhost:5000` and the frontend on `http://localhost:3000`.