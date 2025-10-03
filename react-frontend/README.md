# React Frontend - AI Business Intelligence Platform

**AI-Generated React Application for Capstone Project Deliverables**

This React frontend was generated using AI assistance to meet the specific deliverable requirements for the AI-Driven Software Engineering Capstone Project.

## 🎯 Deliverable Requirements Met

✅ **React Frontend Application** - Complete React app with modern components  
✅ **API Integration** - Connects to FastAPI backend  
✅ **AI-Generated Components** - All components generated with AI assistance  
✅ **Modern UI Design** - Glassmorphism design with Tailwind CSS styling  
✅ **Business Intelligence Features** - Chat, company management, data visualization  

## 🚀 Features

### Core Components (AI-Generated)
- **App.js** - Main application with state management
- **ChatInterface** - AI-powered business intelligence chat
- **CompanyManager** - Company creation and management
- **DatabaseViewer** - Database schema and data exploration
- **Navigation** - Modern glassmorphism navigation

### Design Features
- **Glassmorphism UI** - Modern glass-like design effects
- **Responsive Layout** - Mobile and desktop optimized
- **Smooth Animations** - CSS transitions and hover effects
- **Loading States** - User feedback for async operations
- **Error Handling** - Graceful error display and recovery

## 🛠️ Installation & Setup

### Prerequisites
- Node.js 16+ and npm
- FastAPI backend running on port 8010

### Install Dependencies
```bash
cd react-frontend
npm install
```

### Development Server
```bash
npm start
```
The app will run on http://localhost:3000

### Build for Production
```bash
npm run build
```

## 🔗 API Integration

The React frontend integrates with the FastAPI backend through these endpoints:

- `GET /api/companies/` - List companies
- `GET /api/companies/current` - Get current company
- `POST /api/companies/{id}/switch` - Switch active company
- `POST /api/v1/database/generate` - Generate new company database
- `POST /api/v1/chat/` - Send business intelligence queries
- `GET /api/v1/data/tables` - List database tables
- `GET /api/v1/data/table/{name}` - Get table data

## 🎨 AI-Generated Design

### Glassmorphism Styling
The entire UI uses glassmorphism design generated with AI prompts:
- Backdrop blur effects
- Translucent glass-like cards
- Gradient backgrounds
- Smooth animations and transitions

### Component Generation Process
Each component was generated using specific AI prompts:

1. **Layout Structure**: "Create React component with modern layout..."
2. **API Integration**: "Add axios calls for FastAPI integration..."
3. **State Management**: "Implement React hooks for state..."
4. **Error Handling**: "Add proper error boundaries and loading states..."
5. **Responsive Design**: "Make components mobile-responsive..."

## 📱 Component Structure

```
src/
├── App.js              # Main application component
├── App.css            # Glassmorphism styles
├── index.js           # React entry point
└── components/
    ├── Navigation.js       # Top navigation bar
    ├── ChatInterface.js    # AI chat for business queries
    ├── CompanyManager.js   # Company CRUD operations
    └── DatabaseViewer.js   # Database exploration
```

## 🎯 Usage

1. **Start the Frontend**: `npm start`
2. **Ensure Backend is Running**: FastAPI on port 8010
3. **Create Company**: Use Company Manager to create business database
4. **Analyze Data**: Use AI Chat to ask business intelligence questions
5. **Explore Database**: View tables and data in Database Viewer

## 🤖 AI Assistance Used

This entire React application was built using AI assistance:

- **Component Generation**: All React components generated with AI
- **CSS Styling**: Glassmorphism styles created with AI prompts
- **API Integration**: Axios calls and error handling AI-generated
- **State Management**: React hooks and state logic AI-assisted
- **Responsive Design**: Mobile-first responsive layout AI-created

## 📋 Capstone Project Context

This React frontend fulfills the capstone project requirement for:
> "A React frontend that interacts with your backend API. At least one key component generated from a design screenshot or mockup."

**Key deliverable components:**
- ✅ Complete React application
- ✅ API integration with FastAPI backend
- ✅ Modern UI components (glassmorphism design)
- ✅ Business intelligence functionality
- ✅ AI-generated codebase with documentation

## 🚀 Future Enhancements

Potential AI-assisted improvements:
- Real-time chat with WebSocket integration
- Advanced data visualization components
- Mobile app conversion with React Native
- Voice interface for business queries
- Advanced analytics dashboards

---

**Built with React 18, AI assistance, and modern web technologies for the AI-Driven Software Engineering Capstone Project 2025**