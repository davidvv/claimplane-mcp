# EasyAirClaim Portal

A modern, responsive single-page application (SPA) for filing flight delay compensation claims. Built with React 18, TypeScript, Tailwind CSS, and powered by OpenAPI-driven development.

## 🚀 Features

- **Multi-step Claim Form**: 4-step wizard with form persistence
- **Flight Lookup**: Real-time flight status checking
- **Eligibility Check**: Automatic compensation calculation
- **Document Upload**: Drag & drop file upload with validation
- **Claim Status Tracking**: Track your claim progress
- **Dark Mode**: Toggle between light and dark themes
- **Mobile Responsive**: Works perfectly on all devices
- **Accessibility**: WCAG 2.1 AA compliant
- **Mock JWT Auth**: Secure authentication system

## 🛠️ Tech Stack

- **Framework**: React 18+ with TypeScript
- **Styling**: Tailwind CSS + Custom Components
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod Validation
- **State**: Zustand + React Context
- **HTTP**: Axios with Interceptors
- **Toasts**: Sonner for notifications
- **Icons**: Lucide React
- **Build**: Vite

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/easyairclaim-portal.git
cd easyairclaim-portal

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

## 🔧 Configuration

Create a `.env` file with your configuration:

```env
# API Configuration
VITE_API_BASE_URL=https://api.easyairclaim.com/v1
VITE_API_KEY=your_api_key_here

# Mock JWT for development (optional)
VITE_MOCK_JWT=your_mock_jwt_token

# Analytics (optional)
VITE_ANALYTICS_ENABLED=false
```

## 🏗️ Project Structure

```
easyairclaim-portal/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Layout.tsx     # Main layout with header/footer
│   │   └── ProgressBar.tsx # Multi-step form progress
│   ├── pages/             # Page components
│   │   ├── Home.tsx       # Landing page
│   │   ├── Auth.tsx       # Login page
│   │   ├── Status.tsx     # Claim status checker
│   │   ├── Success.tsx    # Success confirmation
│   │   └── ClaimForm/     # Multi-step claim form
│   │       ├── Step1_Flight.tsx
│   │       ├── Step2_Eligibility.tsx
│   │       ├── Step3_Passenger.tsx
│   │       └── Step4_Review.tsx
│   ├── services/          # API service layer
│   │   ├── api.ts         # Axios instance with interceptors
│   │   ├── flights.ts     # Flight API calls
│   │   ├── eligibility.ts # Eligibility checking
│   │   ├── claims.ts      # Claim management
│   │   └── documents.ts   # Document upload
│   ├── contexts/          # React contexts
│   │   ├── AuthContext.tsx # Authentication
│   │   └── ThemeContext.tsx # Dark mode toggle
│   ├── hooks/             # Custom React hooks
│   │   └── useLocalStorageForm.ts # Form persistence
│   ├── types/             # TypeScript interfaces
│   │   └── openapi.ts     # Generated from OpenAPI spec
│   ├── schemas/           # Zod validation schemas
│   │   └── index.ts       # Form validation rules
│   └── index.css          # Global styles + Tailwind
├── types/
│   └── openapi.d.ts       # Generated TypeScript definitions
├── package.json
├── vite.config.ts
├── tailwind.config.ts
└── README.md
```

## 🎯 Core Features

### Flight Lookup
- Search flights by number and date
- Real-time flight status information
- Delay detection and calculation
- Mock data fallback for development

### Eligibility Check
- Automatic compensation calculation
- EU261, DOT, and CTA regulation support
- Multi-region compensation rules
- Real-time eligibility assessment

### Document Upload
- Drag & drop file upload
- Multiple file format support (PDF, JPG, PNG)
- File size validation (10MB limit)
- Upload progress tracking
- Document preview

### Form Persistence
- LocalStorage-based form data persistence
- Auto-save functionality
- Resume on page refresh
- Step completion tracking

## 🔒 Security Features

- Input sanitization and validation
- XSS prevention
- File type and size validation
- Rate limiting with user-friendly messages
- JWT-based authentication (mock implementation)

## ♿ Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation support
- Screen reader compatible
- High contrast mode support
- ARIA labels and roles
- Focus management

## 📱 Responsive Design

- Mobile-first approach
- Breakpoint-based responsive design
- Touch-friendly interface
- Optimized for all screen sizes
- Progressive enhancement

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Netlify
```bash
# Build the project
npm run build

# Deploy to Netlify
# Drag and drop the dist folder to Netlify
```

### Docker
```bash
# Build Docker image
docker build -t easyairclaim-portal .

# Run container
docker run -p 3000:3000 easyairclaim-portal
```

## 🔧 Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

### Code Quality

- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Husky for git hooks
- Conventional commits

## 📊 Analytics

The app includes analytics stubs for tracking user interactions:

```javascript
// Example usage
if (window.analytics) {
  window.analytics.track('claim_submitted', {
    flight_number: 'LH1234',
    compensation_amount: 600,
    region: 'EU'
  });
}
```

## 🧪 Testing

```bash
# Run unit tests
npm run test

# Run e2e tests
npm run test:e2e

# Run all tests
npm run test:all
```

## 📚 API Integration

The app integrates with the EasyAirClaim API using OpenAPI 3.0.3 specification:

### Authentication
- API Key authentication via `X-API-Key` header
- JWT Bearer token for protected endpoints
- Automatic token refresh

### Error Handling
- User-friendly error messages
- Automatic retry logic
- Network error handling
- Rate limiting support

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@easyairclaim.com or join our Slack channel.

## 🙏 Acknowledgments

- React team for the amazing framework
- Tailwind CSS for the utility-first approach
- Vite for the blazing-fast build tool
- OpenAPI community for the specification
- All contributors and users of this project

---

Made with ❤️ by the EasyAirClaim Team