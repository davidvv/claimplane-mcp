# EasyAirClaim Portal

A modern, production-ready single-page application (SPA) for filing and tracking flight compensation claims across Europe, USA, and Canada.

## Features

- **Multi-Step Claim Form**: Guided wizard for submitting compensation claims
- **Flight Status Lookup**: Real-time flight data integration
- **Eligibility Checker**: Automatic compensation calculation based on EU261/DOT/CTA regulations
- **Claim Status Tracking**: Monitor your claim progress with visual timeline
- **Document Upload**: Drag-and-drop file uploads with validation
- **Dark Mode**: Full dark mode support with persistence
- **Fully Responsive**: Mobile-first design, works on all devices
- **Type-Safe**: 100% TypeScript with auto-generated types from OpenAPI
- **Accessible**: WCAG 2.1 AA compliant

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod validation
- **State**: Zustand
- **HTTP Client**: Axios
- **UI Components**: Custom components with Lucide icons
- **File Upload**: React Dropzone
- **Notifications**: Sonner
- **Build Tool**: Vite

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running (or configure to use staging/production API)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FrontEnd_Claude
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your API configuration:
   ```env
   VITE_API_BASE_URL=https://api.easyairclaim.com/v1
   VITE_API_KEY=your_api_key_here
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   The app will be available at [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
FrontEnd_Claude/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ui/          # Base UI components (Button, Card, Input, etc.)
│   │   └── Layout.tsx   # Main layout with header/footer
│   ├── pages/           # Route pages
│   │   ├── ClaimForm/   # Multi-step claim wizard
│   │   ├── Home.tsx     # Landing page
│   │   ├── Status.tsx   # Claim status tracker
│   │   ├── Success.tsx  # Success confirmation
│   │   └── Auth.tsx     # Authentication (stub)
│   ├── services/        # API service layer
│   │   ├── api.ts       # Axios instance & interceptors
│   │   ├── flights.ts   # Flight operations
│   │   ├── eligibility.ts
│   │   ├── claims.ts
│   │   └── documents.ts
│   ├── schemas/         # Zod validation schemas
│   ├── types/           # TypeScript type definitions
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utility functions
│   ├── store/           # Zustand state management
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

## Key Features Explained

### 1. Multi-Step Claim Form

The claim submission process is divided into 4 steps:

1. **Flight Lookup**: Enter flight number and date
2. **Eligibility Check**: Automatic compensation calculation
3. **Passenger Info**: Contact details and address
4. **Review & Submit**: Final review and document upload

Progress is saved to localStorage, allowing users to resume if they close the browser.

### 2. Type-Safe API Integration

All API types are auto-generated from the OpenAPI 3.0.3 specification:

```typescript
// Types are fully typed from OpenAPI schema
const claim: Claim = await claimService.getClaim(claimId);
```

### 3. Form Validation

Client-side validation using Zod schemas derived from OpenAPI:

```typescript
// Automatic validation with helpful error messages
const schema = Step3PassengerInfoSchema;
```

### 4. Dark Mode

Dark mode is implemented with Tailwind CSS and persists across sessions:

```typescript
const { isDark, toggleDarkMode } = useDarkMode();
```

### 5. Accessibility

- Semantic HTML
- ARIA labels and roles
- Keyboard navigation support
- Screen reader friendly
- Color contrast WCAG AA compliant

## API Integration

### Base Configuration

API calls are configured via environment variables:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const API_KEY = import.meta.env.VITE_API_KEY;
```

### Authentication

The app includes a stub authentication system. In production, this will be replaced with JWT-based auth:

```typescript
// Current: Mock login
// Phase 3: JWT with refresh tokens
```

### Error Handling

Global error handling via Axios interceptors:

- 400: Validation errors → User-friendly messages
- 401: Unauthorized → Redirect to login
- 404: Not found → Toast notification
- 429: Rate limited → Retry message
- 500+: Server errors → Generic error message

## Deployment

### Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_BASE_URL` | Backend API URL | Yes |
| `VITE_API_KEY` | API authentication key | Yes |
| `VITE_ANALYTICS_ENABLED` | Enable analytics tracking | No |
| `VITE_ANALYTICS_KEY` | Analytics service key | No |

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Private - All rights reserved

## Support

For support, email easyairclaim@gmail.com or open an issue in the repository.

## Roadmap

### Phase 3 (Upcoming)
- [ ] JWT authentication implementation
- [ ] User registration and profile management
- [ ] Password reset flow
- [ ] Email verification
- [ ] Admin dashboard access

### Future Features
- [ ] Multi-language support (i18n)
- [ ] PDF claim receipt generation
- [ ] Real-time notifications
- [ ] Live chat support
- [ ] Mobile app (React Native)

## Acknowledgments

- OpenAPI specification for type generation
- Tailwind CSS for styling
- React ecosystem for amazing tools
