# EasyAirClaim Portal

A production-ready React TypeScript SPA for flight compensation claims, integrating with the EasyAirClaim API.

## Features

- **Flight Status Check**: Verify flight details and current status
- **Eligibility Verification**: Check compensation eligibility under EU261, DOT, and CTA regulations
- **Claim Submission**: Submit compensation claims with document uploads
- **Claim Status Tracking**: Monitor claim progress and download documents
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Type Safety**: Full TypeScript integration with API types
- **Form Validation**: Zod schema validation for all forms
- **Error Handling**: Comprehensive error states and loading indicators

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **React Router** for navigation
- **TanStack Query** for API state management
- **Tailwind CSS** for styling
- **Zod** for validation
- **Axios** for HTTP requests

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Access to EasyAirClaim API

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd easyairclaim/FrontEnd
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Configure environment variables in `.env`:
   ```env
   VITE_API_BASE_URL=https://api.easyairclaim.com/v1
   VITE_API_KEY=your-api-key-here
   ```

5. Start development server:
   ```bash
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000) in your browser

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.tsx      # Main layout with navigation
├── lib/                # Utilities and services
│   ├── api.ts          # API client configuration
│   └── validation.ts   # Zod validation schemas
├── pages/              # Route components
│   ├── Home.tsx        # Landing page
│   ├── FlightStatus.tsx # Flight status checker
│   ├── EligibilityCheck.tsx # Eligibility verification
│   ├── ClaimSubmission.tsx # Claim submission form
│   └── ClaimStatus.tsx # Claim status tracker
├── types/              # TypeScript type definitions
│   └── api.ts          # API response types
├── App.tsx             # Main app component
├── main.tsx            # App entry point
└── index.css           # Global styles
```

## API Integration

The app integrates with the EasyAirClaim API endpoints:

- `GET /flights/status/{flightNumber}` - Flight status lookup
- `POST /eligibility/check` - Eligibility verification
- `POST /claims` - Claim submission
- `GET /claims/{claimId}` - Claim status retrieval
- `POST /claims/{claimId}/documents` - Document upload
- `GET /documents/{documentId}` - Document download

## Validation

Form validation is handled by Zod schemas in `src/lib/validation.ts`:

- Flight number format validation
- Email format validation
- Airport code validation (IATA format)
- Required field validation
- String length limits

## Styling

The app uses Tailwind CSS with custom component classes defined in `src/index.css`:

- `.btn` - Primary button style
- `.btn-secondary` - Secondary button style
- `.input` - Form input styling
- `.card` - Card container styling

## Error Handling

Comprehensive error handling includes:

- API error responses
- Network error handling
- Form validation errors
- Loading states for all async operations
- User-friendly error messages

## Accessibility

The app includes accessibility features:

- Semantic HTML elements
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader friendly content
- Focus management

## Production Deployment

1. Build the app:
   ```bash
   npm run build
   ```

2. The build artifacts will be stored in the `dist/` directory.

3. Serve the `dist` folder with any static hosting service.

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Ensure TypeScript types are properly defined

## License

Private - EasyAirClaim