# Coffy ☕

A modern, AI-powered event scheduling and management platform that uses an LLM agent system to automate the entire event planning process. The platform intelligently handles event creation, participant coordination, and scheduling through natural language interactions.

## 🌟 Core Features

### AI-Powered Event Management
- LLM agent system using OpenRouter's Qwen-Turbo model
- Multi-stage conversation flow for event planning
- Intelligent tool-calling system for automated actions
- Natural language processing for participant interactions
- Real-time availability coordination

### Event Planning Workflow
1. **Event Creation**
   - Natural language event creation
   - Smart contact selection and invitation
   - Automated participant registration check
   - Intelligent conversation management

2. **Participant Coordination**
   - Automated SMS notifications
   - Smart confirmation handling
   - Intelligent response parsing
   - Multi-participant coordination

3. **Availability Collection**
   - Google Calendar integration for registered users
   - Natural language availability parsing for unregistered users
   - Smart time slot management
   - Conflict resolution

4. **Scheduling**
   - Optimal time slot selection
   - Automated calendar event creation
   - Multi-participant notification
   - Schedule conflict handling

### Web Platform
- Next.js 15 with TypeScript
- Real-time WebSocket communication
- Beautiful UI with shadcn/ui and Tailwind CSS
- Interactive chat interface
- Real-time event status updates

### Mobile App
- React Native with Expo
- Cross-platform compatibility
- Push notifications
- Real-time chat interface
- Calendar integration

### Backend Services
- Python FastAPI backend
- PostgreSQL database
- Redis caching
- WebSocket support for real-time updates
- SMS integration for notifications
- Google Calendar API integration

## 🛠️ Technical Architecture

### AI/LLM Components
- OpenRouter API integration
- Custom tool-calling system
- Multi-stage conversation management
- Intelligent prompt engineering
- Context-aware responses

### Communication Layer
- WebSocket for real-time updates
- SMS gateway integration
- Push notification system
- Email notifications

### Data Management
- PostgreSQL for persistent storage
- Redis for caching and real-time data
- Google Calendar API integration
- Contact management system

## 🚀 Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Python 3.8+
- Bun package manager
- Expo CLI
- PostgreSQL
- Redis
- OpenRouter API key
- Google Calendar API credentials
- SMS gateway credentials

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

## 🔧 Environment Variables

### Web
```
NEXT_PUBLIC_API_URL=your_api_url
NEXT_PUBLIC_WS_URL=your_websocket_url
```

### Mobile
```
EXPO_PUBLIC_API_URL=your_api_url
EXPO_PUBLIC_WS_URL=your_websocket_url
```

### Backend
```
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_CALENDAR_CREDENTIALS=your_google_credentials
SMS_GATEWAY_CREDENTIALS=your_sms_credentials
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