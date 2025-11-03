# EasyAirClaim Portal - Complete Project Structure

## File Tree

```
FrontEnd_Claude/
│
├── 📄 Configuration Files
│   ├── package.json              # Dependencies and scripts
│   ├── vite.config.ts            # Vite build configuration
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tsconfig.node.json        # TypeScript config for Vite
│   ├── tailwind.config.ts        # Tailwind CSS configuration
│   ├── postcss.config.js         # PostCSS configuration
│   ├── .eslintrc.cjs             # ESLint rules
│   ├── .env.example              # Environment variables template
│   └── .gitignore                # Git ignore rules
│
├── 📚 Documentation
│   ├── README.md                 # Full project documentation
│   ├── QUICKSTART.md             # 5-minute setup guide
│   ├── DEPLOYMENT.md             # Deployment instructions
│   ├── PROJECT_SUMMARY.md        # Executive summary
│   ├── PROJECT_STRUCTURE.md      # This file
│   └── CHANGELOG.md              # Version history
│
├── 🛠️ Setup Scripts
│   ├── setup.sh                  # Setup script (Linux/Mac)
│   └── setup.bat                 # Setup script (Windows)
│
├── 📁 public/
│   ├── plane-icon.svg            # Favicon
│   └── (static assets)
│
└── 📁 src/
    │
    ├── 🎨 Components
    │   ├── Layout.tsx                    # Main layout (header/footer)
    │   └── ui/
    │       ├── Button.tsx                # Reusable button component
    │       ├── Card.tsx                  # Card container component
    │       ├── Input.tsx                 # Form input with validation
    │       ├── Select.tsx                # Dropdown select component
    │       ├── Badge.tsx                 # Status badge component
    │       ├── Loading.tsx               # Spinners and skeletons
    │       ├── ProgressBar.tsx           # Wizard progress indicator
    │       └── FileUpload.tsx            # Drag-and-drop file uploader
    │
    ├── 📄 Pages
    │   ├── Home.tsx                      # Landing page
    │   ├── Status.tsx                    # Claim status tracker
    │   ├── Success.tsx                   # Success confirmation page
    │   ├── Auth.tsx                      # Authentication (stub)
    │   └── ClaimForm/
    │       ├── index.tsx                 # Wizard container
    │       ├── Step1_Flight.tsx          # Flight lookup step
    │       ├── Step2_Eligibility.tsx     # Eligibility check step
    │       ├── Step3_Passenger.tsx       # Passenger info step
    │       └── Step4_Review.tsx          # Review and submit step
    │
    ├── 🔌 Services (API Layer)
    │   ├── api.ts                        # Axios instance & interceptors
    │   ├── flights.ts                    # Flight API calls
    │   ├── eligibility.ts                # Eligibility API calls
    │   ├── claims.ts                     # Claims API calls
    │   ├── customers.ts                  # Customers API calls
    │   └── documents.ts                  # Documents API calls
    │
    ├── 📋 Schemas
    │   └── validation.ts                 # Zod validation schemas
    │
    ├── 🔤 Types
    │   └── openapi.ts                    # TypeScript types from OpenAPI
    │
    ├── 🎣 Hooks
    │   ├── useLocalStorage.ts            # LocalStorage hook
    │   └── useDarkMode.ts                # Dark mode hook
    │
    ├── 🛠️ Utilities
    │   └── utils.ts                      # Helper functions
    │
    ├── 🗄️ Store
    │   └── claimStore.ts                 # Zustand state management
    │
    ├── 🎯 Entry Points
    │   ├── App.tsx                       # Main app component
    │   ├── main.tsx                      # React entry point
    │   ├── index.css                     # Global styles
    │   └── vite-env.d.ts                 # Vite environment types
    │
    └── (Build output in dist/ after npm run build)
```

## File Count Summary

| Category | Count | Files |
|----------|-------|-------|
| **Pages** | 9 | Home, Status, Success, Auth, + 4 wizard steps + index |
| **UI Components** | 9 | Layout + 8 reusable components |
| **Services** | 6 | API + 5 domain services |
| **Schemas** | 1 | Zod validation schemas |
| **Types** | 1 | OpenAPI TypeScript types |
| **Hooks** | 2 | LocalStorage + DarkMode |
| **Store** | 1 | Zustand claim store |
| **Utilities** | 1 | Helper functions |
| **Config** | 9 | Vite, TS, Tailwind, ESLint, etc. |
| **Docs** | 6 | README, guides, changelog |
| **Scripts** | 2 | Setup scripts |
| **Total** | 47 | Source + config + docs |

## Component Hierarchy

```
App (BrowserRouter)
└── Layout
    ├── Header
    │   ├── Logo (Link to /)
    │   ├── Navigation
    │   │   ├── /claim (Link)
    │   │   └── /status (Link)
    │   └── Actions
    │       ├── Dark Mode Toggle
    │       └── Auth (Login/Logout)
    │
    ├── Main (Routes)
    │   ├── / → HomePage
    │   ├── /claim → ClaimFormPage
    │   │   └── ProgressBar
    │   │       ├── Step 0 → Step1_Flight
    │   │       ├── Step 1 → Step2_Eligibility
    │   │       ├── Step 2 → Step3_Passenger
    │   │       └── Step 3 → Step4_Review
    │   ├── /status → StatusPage
    │   ├── /success → SuccessPage
    │   └── /auth → AuthPage
    │
    └── Footer
        ├── About
        ├── Quick Links
        ├── Legal
        └── Contact
```

## Data Flow

```
User Input
    ↓
React Component
    ↓
React Hook Form
    ↓
Zod Validation
    ↓
[Valid?]
    ├─ No → Display Errors
    └─ Yes ↓
         API Service
             ↓
         Axios Instance
             ↓
         Request Interceptor (+ auth)
             ↓
         Backend API
             ↓
         Response Interceptor (error handling)
             ↓
         [Success?]
             ├─ No → Toast Error
             └─ Yes ↓
                  Update UI
                      ↓
                  Toast Success
```

## State Management Strategy

### 1. **Local Component State** (useState)
- UI state (open/closed, hover, etc.)
- Form field values (React Hook Form)
- Loading states
- Error messages

### 2. **Zustand Store** (Global)
- Multi-step form state (`claimStore`)
- Current wizard step
- Form data across steps

### 3. **LocalStorage** (Persistent)
- Dark mode preference
- Form progress (auto-save)
- Auth token (mock)
- User preferences

### 4. **URL State** (Router)
- Current page
- Query parameters (e.g., claimId)

## API Integration Architecture

```
┌─────────────────────────────────────────┐
│     OpenAPI 3.0.3 Specification         │
│   (Single Source of Truth)              │
└─────────────┬───────────────────────────┘
              │
              ├──► TypeScript Types (src/types/openapi.ts)
              │    └─ Interfaces for all API entities
              │
              ├──► Zod Schemas (src/schemas/validation.ts)
              │    └─ Form validation rules
              │
              └──► API Services (src/services/*.ts)
                   ├─ flights.ts
                   ├─ eligibility.ts
                   ├─ claims.ts
                   ├─ customers.ts
                   └─ documents.ts
                        │
                        ▼
              ┌───────────────────────┐
              │   Axios Instance      │
              │  (src/services/api.ts)│
              └───────────────────────┘
                        │
                ┌───────┴───────┐
                ▼               ▼
      Request Interceptor   Response Interceptor
      (Add auth token)      (Error handling)
                │               │
                └───────┬───────┘
                        ▼
              ┌───────────────────────┐
              │    Backend API        │
              └───────────────────────┘
```

## Routing Structure

| Route | Component | Purpose | Auth Required |
|-------|-----------|---------|---------------|
| `/` | HomePage | Landing page | No |
| `/claim` | ClaimFormPage | Multi-step claim wizard | No |
| `/status` | StatusPage | Claim status lookup | No |
| `/success` | SuccessPage | Claim confirmation | No |
| `/auth` | AuthPage | Login (stub) | No |
| `*` | Navigate to `/` | 404 fallback | No |

## Form Validation Flow

```
User Input
    ↓
onChange Event
    ↓
React Hook Form (register)
    ↓
Zod Schema Validation
    │
    ├─ Field-level (on blur)
    └─ Form-level (on submit)
        │
        ├─ Invalid → Set errors
        │              ├─ Display inline errors
        │              └─ Toast notification
        │
        └─ Valid → Call API
                       │
                       ├─ Success → Navigate/Update UI
                       └─ Error → Toast + Set form error
```

## Build Process

```
Source Code (src/)
    ↓
TypeScript Compiler
    ↓
Vite Build
    ├─ Tree Shaking
    ├─ Code Splitting
    ├─ Minification
    └─ Asset Optimization
        ↓
    dist/
    ├── index.html
    ├── assets/
    │   ├── index-[hash].js
    │   ├── index-[hash].css
    │   └── (images, fonts)
    └── (ready for deployment)
```

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `VITE_API_BASE_URL` | Yes | - | Backend API URL |
| `VITE_API_KEY` | Yes | - | API authentication |
| `VITE_ANALYTICS_ENABLED` | No | `false` | Enable analytics |
| `VITE_ANALYTICS_KEY` | No | - | Analytics key |

## Dependencies Summary

### Production Dependencies (18)
- **react** & **react-dom** - UI framework
- **react-router-dom** - Routing
- **react-hook-form** - Form management
- **zod** - Validation
- **@hookform/resolvers** - Zod + RHF integration
- **axios** - HTTP client
- **zustand** - State management
- **sonner** - Toast notifications
- **lucide-react** - Icons
- **clsx** & **tailwind-merge** - CSS utilities
- **date-fns** - Date formatting
- **react-dropzone** - File uploads

### Dev Dependencies (13)
- **typescript** - Type system
- **vite** - Build tool
- **@vitejs/plugin-react** - Vite React plugin
- **tailwindcss** - CSS framework
- **autoprefixer** - CSS vendor prefixes
- **postcss** - CSS processing
- **eslint** - Code linting
- **@typescript-eslint/*** - TS ESLint
- **@types/*** - TypeScript types

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run type-check` | TypeScript type checking |

## Code Style

- **Naming**: camelCase variables, PascalCase components
- **Imports**: Absolute paths with `@/` alias
- **Comments**: JSDoc for functions, inline for complex logic
- **Formatting**: 2-space indent, single quotes, semicolons
- **Files**: One component per file, named exports for utils

## Testing Strategy (Future)

```
Unit Tests (Vitest)
├── Components (UI rendering)
├── Hooks (custom hooks)
├── Utils (helper functions)
└── Services (API mocking)

E2E Tests (Playwright)
├── User flows (claim submission)
├── Form validation
├── Navigation
└── Error handling
```

## Performance Optimizations

1. **Code Splitting**: Routes lazy-loaded
2. **Tree Shaking**: Unused code removed
3. **Minification**: JS/CSS compressed
4. **Lazy Images**: Load on viewport
5. **Memoization**: useMemo, useCallback where needed
6. **Bundle Analysis**: Vite rollup options

---

**Last Updated**: 2025-11-01
**Version**: 1.0.0
**Status**: Production Ready ✅
