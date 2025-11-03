# Quick Start Guide

Get the EasyAirClaim Portal running in under 5 minutes!

## Installation

```bash
# 1. Install dependencies
npm install

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and add your API credentials
# VITE_API_BASE_URL=https://api.easyairclaim.com/v1
# VITE_API_KEY=your_api_key_here

# 4. Start development server
npm run dev
```

The app will open at [http://localhost:3000](http://localhost:3000)

## What You Get

### Home Page (/)
- Hero section with CTAs
- "How it works" section
- Compensation amounts table
- FAQs

### File a Claim (/claim)
**4-Step Wizard:**
1. Flight Lookup - Enter flight number and date
2. Eligibility Check - Automatic compensation calculation
3. Passenger Info - Your contact details
4. Review & Submit - Final review and document upload

### Check Status (/status)
- Enter Claim ID
- View claim timeline
- Download documents
- See compensation amount

### Success Page (/success)
- Confirmation message
- Claim ID display
- Next steps guide

### Authentication (/auth)
- Mock login (stub for Phase 3)
- Any email/password works in development

## Testing the App

### Test Flow 1: Submit a Claim

1. Go to `/claim`
2. Enter flight details:
   - Flight Number: `LH1234`
   - Date: Any recent date
3. Click "Search Flight"
4. Review eligibility
5. Fill passenger info
6. Submit claim
7. Get Claim ID

### Test Flow 2: Check Status

1. Go to `/status`
2. Enter the Claim ID from above
3. View claim details and timeline

### Test Flow 3: Dark Mode

1. Click moon/sun icon in header
2. Theme persists across refreshes

## Key Features to Explore

- **Form Validation**: Try submitting empty fields
- **Error Handling**: Enter invalid flight number
- **File Upload**: Drag & drop a PDF in review step
- **Responsive Design**: Resize browser or use mobile
- **Accessibility**: Try keyboard navigation (Tab key)
- **Local Storage**: Refresh during claim form - progress is saved!

## Common Development Tasks

### Run Tests
```bash
npm test
```

### Type Check
```bash
npm run type-check
```

### Lint Code
```bash
npm run lint
```

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Project Structure

```
src/
├── components/ui/    ← Reusable UI components
├── pages/            ← Route pages
├── services/         ← API calls
├── schemas/          ← Zod validation
├── types/            ← TypeScript types
├── hooks/            ← Custom hooks
├── lib/              ← Utilities
└── store/            ← State management
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Backend API URL |
| `VITE_API_KEY` | Yes | API authentication key |
| `VITE_ANALYTICS_ENABLED` | No | Enable analytics (default: false) |

## Browser DevTools

Open DevTools (F12) to see:
- Console: API calls and events
- Network: Request/response data
- Application → Local Storage: Form data and auth token

## Next Steps

1. Review [README.md](./README.md) for full documentation
2. Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment guides
3. Explore the code structure
4. Customize styling in `tailwind.config.ts`
5. Add your own components in `src/components/`

## Troubleshooting

### Port 3000 already in use?
```bash
# Edit vite.config.ts and change port, or:
npm run dev -- --port 3001
```

### TypeScript errors?
```bash
npm run type-check
```

### API calls failing?
1. Check `.env` file exists and has correct values
2. Verify backend is running
3. Check browser console for CORS errors

### Styles not working?
```bash
# Restart dev server
npm run dev
```

## Need Help?

- Email: easyairclaim@gmail.com
- GitHub Issues: [Create an issue](https://github.com/...)
- Documentation: See README.md

---

**You're all set!** Start building. 🚀
