# KioskAI Frontend

Modern, responsive dashboard for managing customer communications.

## Features

- 🎨 **Beautiful UI** - Deep Royal Blue, Soft Gold, and Teal color scheme
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- ⚡ **Fast & Smooth** - Optimized animations and transitions
- 🔐 **Secure Authentication** - JWT-based auth with token management
- 📊 **Real-time Analytics** - Live dashboard metrics
- 💬 **Message Management** - View and manage customer conversations
- 👥 **Customer Tracking** - Complete customer profiles and history
- 💰 **Invoice Management** - Create and send payment links

## Tech Stack

- **HTML5** - Semantic markup
- **CSS3** - Custom design system with CSS variables
- **Vanilla JavaScript** - No frameworks, pure performance
- **Google Fonts** - Inter font family

## Setup

### Development

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Serve locally** (using Python):
```bash
python -m http.server 3000
```

Or using Node.js:
```bash
npx serve -p 3000
```

3. **Open browser**:
```
http://localhost:3000
```

### Configuration

Update the API base URL in `js/app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000'; // Change for production
```

## Project Structure

```
frontend/
├── index.html          # Main HTML file
├── css/
│   └── index.css       # Complete design system
└── js/
    └── app.js          # Application logic
```

## Design System

### Color Palette

- **Primary (Deep Royal Blue)**: `#1e3a8a`
- **Accent (Soft Gold)**: `#d4af37`
- **Interactive (Teal)**: `#14b8a6`
- **Background**: `#f8f9fa`
- **Text Primary**: `#1f2937`
- **Text Secondary**: `#6b7280`

### Typography

- **Font Family**: Inter
- **Sizes**: 0.75rem - 1.875rem
- **Weights**: 300, 400, 500, 600, 700

### Components

- Authentication screens
- Dashboard layout with sidebar
- Metric cards with hover effects
- Data tables with sorting
- Message threads
- Notification toasts
- Responsive navigation

## Features

### Authentication

- Login with email/password
- Registration with business details
- JWT token management
- Auto-redirect on session expiry

### Dashboard

- **Overview**: Key metrics and insights
- **Customers**: Full customer management
- **Messages**: Conversation threads
- **Orders**: Order tracking and management
- **Invoices**: Invoice creation and sending

### Responsive Design

- Desktop: Full sidebar navigation
- Tablet: Collapsible sidebar
- Mobile: Bottom navigation

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- No external dependencies (except Google Fonts)
- Optimized animations with CSS transforms
- Lazy loading for data tables
- Efficient DOM manipulation

## Deployment

### Static Hosting

Deploy to any static hosting service:

- **Vercel**: `vercel deploy`
- **Netlify**: Drag and drop `frontend` folder
- **GitHub Pages**: Push to `gh-pages` branch

### Production Build

For production, update:

1. API base URL in `app.js`
2. Remove console.log statements
3. Minify CSS and JS (optional)

## License

Proprietary - KioskAI
