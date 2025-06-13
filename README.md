# Coffy ☕

A modern, full-stack coffee shop management and ordering platform built with Next.js, React Native, and Python.

## 🌟 Features

### Web Platform
- Modern, responsive web interface built with Next.js
- Beautiful UI components using shadcn/ui and Tailwind CSS
- Real-time order tracking and management
- Interactive menu management system
- Customer analytics dashboard
- Staff management interface

### Mobile App
- Cross-platform mobile application built with React Native
- Real-time order placement and tracking
- Push notifications for order updates
- Digital loyalty program
- Mobile payments integration
- Location-based store finder

### Backend Services
- Robust Python-based backend API
- Real-time data synchronization
- Secure authentication and authorization
- Database management and optimization
- Automated order processing system

## 🛠️ Tech Stack

### Web Frontend
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- Biome (Linting & Formatting)

### Mobile App
- React Native
- Expo
- TypeScript
- Custom hooks and components
- Native device features integration

### Backend
- Python
- FastAPI/Django
- PostgreSQL
- Redis (for caching)
- WebSocket support

## 🚀 Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Python 3.8+
- Bun package manager
- Expo CLI
- PostgreSQL

### Web Development
```bash
cd web
bun install
bun run dev
```

### Mobile Development
```bash
cd mobile/frontend
npm install
npx expo start
```

### Backend Development
```bash
cd mobile/backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

## 📱 Mobile App Setup

1. Install Expo Go on your mobile device
2. Scan the QR code from the Expo development server
3. The app will load on your device

## 🌐 Web App Setup

1. Open your browser and navigate to `http://localhost:3000`
2. The web interface will be available for testing

## 🔧 Environment Variables

Create `.env` files in the respective directories with the following variables:

### Web
```
NEXT_PUBLIC_API_URL=your_api_url
```

### Mobile
```
EXPO_PUBLIC_API_URL=your_api_url
```

### Backend
```
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

## 📦 Deployment

### Web
- Deployed on Netlify
- Automatic deployments from main branch
- Preview deployments for pull requests

### Mobile
- iOS: App Store
- Android: Google Play Store
- EAS Build for production builds

### Backend
- Deployed on Railway
- Automatic deployments from main branch
- Database backups configured

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- Frontend Developers
- Backend Developers
- Mobile Developers
- UI/UX Designers
- Project Managers