# 🦆 Ducks Trainer Portal

A comprehensive fitness training portal built with React and Flask, featuring real-time messaging, workout tracking, nutrition monitoring, and progress analytics.

## 🚀 Live Demo

**Frontend**: [https://ducks-trainer-portal.vercel.app](https://ducks-trainer-portal.vercel.app)
**Backend API**: [https://ducks-trainer-portal.vercel.app/api](https://ducks-trainer-portal.vercel.app/api)

## ✨ Features

- 🏋️ **Workout Tracking** - Complete workout management with rest timers and progress logging
- 💬 **Real-time Chat** - Live messaging between trainers and clients
- 🍎 **Nutrition Tracking** - Comprehensive macro and calorie monitoring
- 📊 **Progress Analytics** - Charts and statistics for body composition and performance
- 🏆 **Achievement System** - Gamified progress tracking with rewards
- 📱 **Mobile Responsive** - Optimized for all devices
- 🔐 **Secure Authentication** - Protected client and trainer portals

## 🛠️ Tech Stack

**Frontend:**
- React 18 with Hooks
- Tailwind CSS for styling
- Framer Motion for animations
- Socket.IO for real-time features
- React Query for data management

**Backend:**
- Flask with SQLAlchemy
- Socket.IO for WebSocket connections
- SQLite database
- Flask-CORS for cross-origin requests

## 📦 Local Development

### Prerequisites
- Node.js 18+
- Python 3.8+
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ducks-trainer-portal.git
   cd ducks-trainer-portal
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd ../backend
   pip install -r requirements.txt
   ```

4. **Start development servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python run.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api

## 🚀 Vercel Deployment

This app is configured for easy deployment on Vercel:

### Quick Deploy
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/ducks-trainer-portal)

### Manual Deployment

1. **Connect to Vercel**
   ```bash
   npm i -g vercel
   vercel login
   ```

2. **Deploy**
   ```bash
   vercel --prod
   ```

3. **Environment Variables**
   The app will automatically configure the necessary environment variables for production.

## 📱 Mobile Access

Once deployed, you can access the app on any device:
- **Smartphones** - Full responsive design
- **Tablets** - Optimized tablet interface
- **Desktop** - Complete desktop experience

## 🔧 Configuration

### Environment Variables

**Frontend** (`frontend/env.production`):
```bash
REACT_APP_API_URL=https://your-app.vercel.app
REACT_APP_SOCKET_URL=https://your-app.vercel.app
```

**Backend**:
```bash
FLASK_ENV=production
DATABASE_URL=sqlite:///database.db
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

## 📊 Database Schema

The app uses SQLite with the following main tables:
- `clients` - User profiles and settings
- `workout_logs` - Exercise performance tracking
- `nutrition_logs` - Food and macro tracking
- `body_stats` - Weight and measurement history
- `messages` - Chat system data
- `achievements` - Gamification rewards

## 🎯 Usage

### For Clients
1. Access your unique client URL
2. View today's workout and nutrition goals
3. Log workouts with rest timers and progress tracking
4. Track nutrition with macro breakdowns
5. Chat with your trainer in real-time
6. View progress analytics and achievements

### For Trainers
1. Manage multiple clients
2. Create and assign workout programs
3. Monitor client progress in real-time
4. Communicate via built-in messaging
5. Track client achievements and milestones

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@duckstrainer.com or join our Discord community.

## 🙏 Acknowledgments

- WGER Exercise Database for exercise data
- React community for excellent documentation
- Flask community for backend framework
- Vercel for seamless deployment platform
