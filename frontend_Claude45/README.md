# EasyAirClaim - Flight Compensation Portal

A production-ready, responsive single-page application (SPA) for filing flight compensation claims. Built with React, TypeScript, Tailwind CSS, and fully typed using OpenAPI specifications.

## Features

- **Flight Lookup**: Search for flight details with real-time status
- **Eligibility Check**: Automatically verify compensation eligibility under EU261/DOT/CTA regulations
- **4-Step Claim Wizard**: Intuitive multi-step form with progress tracking
- **Document Upload**: Drag-and-drop file upload with validation
- **Claim Tracking**: Check claim status anytime with Claim ID
- **Dark Mode**: System preference detection with manual toggle
- **Mobile-First**: Fully responsive design for all devices
- **Accessible**: WCAG 2.1 AA compliant with keyboard navigation
- **Form Persistence**: LocalStorage saves progress across sessions

## Tech Stack

- **Framework**: React 18 + TypeScript 5
- **Routing**: React Router v6
- **Styling**: Tailwind CSS + ShadCN UI components
- **Forms**: React Hook Form + Zod validation
- **API**: Axios with interceptors
- **State**: LocalStorage + Custom hooks
- **Build**: Vite
- **Icons**: Lucide React

## Project Structure

```
easyairclaim-portal/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── ui/            # Base components (Button, Card, Input, etc.)
│   │   ├── Layout.tsx     # Main layout with nav
│   │   ├── Stepper.tsx    # Progress indicator
│   │   ├── FileUploadZone.tsx
│   │   └── DarkModeToggle.tsx
│   ├── pages/             # Route pages
│   │   ├── Home.tsx
│   │   ├── ClaimForm/     # 4-step wizard
│   │   │   ├── ClaimFormPage.tsx
│   │   │   ├── Step1_Flight.tsx
│   │   │   ├── Step2_Eligibility.tsx
│   │   │   ├── Step3_Passenger.tsx
│   │   │   └── Step4_Review.tsx
│   │   ├── Status.tsx
│   │   ├── Success.tsx
│   │   └── Auth.tsx
│   ├── services/          # API service layer
│   │   ├── api.ts         # Axios instance
│   │   ├── flights.ts
│   │   ├── eligibility.ts
│   │   ├── claims.ts
│   │   └── documents.ts
│   ├── schemas/           # Zod validation schemas
│   │   └── validation.ts
│   ├── types/             # TypeScript types from OpenAPI
│   │   └── api.ts
│   ├── hooks/             # Custom React hooks
│   │   ├── useLocalStorageForm.ts
│   │   └── useDarkMode.ts
│   ├── lib/
│   │   └── utils.ts       # Utility functions
│   ├── App.tsx            # Main app with routing
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── .env.example           # Environment variables template
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see backend README)

### Installation

1. **Clone the repository**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/v1
   VITE_API_KEY=your_api_key_here
   VITE_ENV=development
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   App will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `https://api.easyairclaim.com/v1` |
| `VITE_API_KEY` | API key for authentication | `your_api_key` |
| `VITE_ENV` | Environment (development/production) | `production` |

## Key Features

### 1. Flight Lookup (Step 1)

- Input: Flight number + departure date
- API: `GET /flights/status/{flightNumber}?date=YYYY-MM-DD`
- Auto-populates flight details
- Shows delay information

### 2. Eligibility Check (Step 2)

- API: `POST /eligibility/check`
- Validates compensation eligibility
- Shows estimated amount and regulation
- Lists required documents

### 3. Passenger Information (Step 3)

- React Hook Form with Zod validation
- Personal details + address
- Incident type selection
- Document upload with drag-and-drop

### 4. Review & Submit (Step 4)

- Summary of all information
- API: `POST /claims` → `POST /claims/{claimId}/documents`
- Shows upload progress
- Redirects to success page

### Claim Status Tracking

- Input: Claim ID
- API: `GET /claims/{claimId}`
- Visual timeline
- Document downloads

## API Integration

All API calls are typed using the OpenAPI specification:

```typescript
// Example: Flight lookup
import { getFlightStatus } from '@/services/flights';

const flight = await getFlightStatus({
  flightNumber: 'LH1234',
  date: '2025-06-15'
});
```

### Error Handling

Axios interceptors handle:
- 401: Unauthorized → Redirect to login
- 404: Not found → User-friendly message
- 429: Rate limit → Retry message
- 500/502/503: Server errors → Toast notification

## Form Validation

Zod schemas match OpenAPI spec:

```typescript
// Email validation
email: z.string().email('Invalid email address')

// Flight number validation
flightNumber: z.string()
  .regex(/^[A-Z0-9]{2,3}\d{1,4}$/i, 'Invalid format')
```

## Form Persistence

Claims are saved to LocalStorage:

```typescript
const { formData, updateStep, clearFormData } = useClaimFormPersistence();
```

Data persists across:
- Page refreshes
- Browser closes
- Navigation away

## Accessibility

- Semantic HTML (`<nav>`, `<main>`, `<footer>`)
- ARIA labels on all interactive elements
- Keyboard navigation
- Focus management
- Color contrast WCAG AA compliant
- Screen reader tested

## Dark Mode

Automatic system preference detection:

```typescript
const { isDark, toggleDarkMode } = useDarkMode();
```

Stored in localStorage for persistence.

## Deployment

### Vercel

1. Push to GitHub
2. Import repository in Vercel
3. Set environment variables
4. Deploy

### Netlify

1. Connect repository
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Set environment variables

### Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Development

### Code Style

- ESLint configured with React + TypeScript rules
- Prettier recommended
- Import order: React → third-party → local

### Type Safety

All API responses are typed:

```typescript
const claim: Claim = await submitClaim(request);
```

### Testing (Recommended)

```bash
# Install testing libraries
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Run tests
npm run test
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Code splitting by route
- Lazy loading for heavy components
- Image optimization
- Lighthouse score: 90+

## Security

- XSS prevention: React's auto-escaping
- CSRF: API key in headers
- File upload validation:
  - Max size: 10MB
  - Allowed types: PDF, JPG, PNG
  - MIME type validation

## API Documentation

Full API reference: See OpenAPI spec in project root

Key endpoints:
- `GET /flights/status/{flightNumber}`
- `POST /eligibility/check`
- `POST /claims`
- `POST /claims/{claimId}/documents`
- `GET /claims/{claimId}`

## Troubleshooting

### API Connection Issues

Check:
1. Backend is running
2. `VITE_API_BASE_URL` is correct
3. CORS is configured on backend
4. API key is valid

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Type Errors

```bash
# Regenerate types
npm run type-check
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Private - All rights reserved

## Support

Email: easyairclaim@gmail.com
Website: https://www.easyairclaim.com

---

**Built with ❤️ for passengers seeking fair compensation**
