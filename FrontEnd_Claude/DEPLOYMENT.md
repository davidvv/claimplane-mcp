# Deployment Guide

This guide covers deploying the EasyAirClaim Portal to various platforms.

## Prerequisites

- Node.js 18+ installed
- Project built successfully (`npm run build`)
- Environment variables configured

## Platform-Specific Guides

### 1. Vercel (Recommended)

Vercel offers the easiest deployment with zero configuration.

#### Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

#### Via Git Integration

1. Push code to GitHub/GitLab/Bitbucket
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Import your repository
5. Configure environment variables:
   - `VITE_API_BASE_URL`
   - `VITE_API_KEY`
6. Click "Deploy"

**Environment Variables in Vercel:**
- Go to Project Settings → Environment Variables
- Add all required variables
- Redeploy to apply changes

---

### 2. Netlify

#### Via Netlify CLI

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Login
netlify login

# Build
npm run build

# Deploy
netlify deploy --prod --dir=dist
```

#### Via Git Integration

1. Push code to repository
2. Go to [netlify.com](https://netlify.com)
3. Click "New site from Git"
4. Select repository
5. Build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
6. Environment variables: Add in Site Settings → Environment
7. Deploy

**netlify.toml** (optional, for configuration):

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

### 3. AWS S3 + CloudFront

#### Build for Production

```bash
npm run build
```

#### Upload to S3

```bash
# Install AWS CLI
aws configure

# Create S3 bucket
aws s3 mb s3://easyairclaim-portal

# Enable static website hosting
aws s3 website s3://easyairclaim-portal \
  --index-document index.html \
  --error-document index.html

# Upload build
aws s3 sync dist/ s3://easyairclaim-portal --delete
```

#### Set Up CloudFront (CDN)

1. Go to AWS CloudFront console
2. Create distribution
3. Origin: Your S3 bucket
4. Default root object: `index.html`
5. Error pages: Redirect 404 to `/index.html` (for SPA routing)
6. SSL/TLS certificate: Use ACM or custom

---

### 4. Docker + Any Cloud Provider

#### Dockerfile

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### nginx.conf

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

#### Build and Run

```bash
# Build image
docker build -t easyairclaim-portal .

# Run container
docker run -p 8080:80 easyairclaim-portal
```

#### Deploy to Cloud

**AWS ECS:**
```bash
aws ecr create-repository --repository-name easyairclaim-portal
docker tag easyairclaim-portal:latest <ECR_URI>
docker push <ECR_URI>
# Create ECS task definition and service
```

**Google Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/easyairclaim-portal
gcloud run deploy --image gcr.io/PROJECT_ID/easyairclaim-portal --platform managed
```

---

### 5. GitHub Pages

**Note:** GitHub Pages requires HashRouter instead of BrowserRouter for SPAs.

#### Modify Router (for GitHub Pages only)

```tsx
// In App.tsx, change:
import { BrowserRouter } from 'react-router-dom';
// to:
import { HashRouter } from 'react-router-dom';

// And use <HashRouter> instead of <BrowserRouter>
```

#### Deploy

```bash
# Install gh-pages
npm install --save-dev gh-pages

# Add to package.json:
{
  "homepage": "https://yourusername.github.io/easyairclaim-portal",
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
  }
}

# Deploy
npm run deploy
```

---

## Environment Variables for Production

Create a `.env.production` file:

```env
VITE_API_BASE_URL=https://api.easyairclaim.com/v1
VITE_API_KEY=production_api_key_here
VITE_ANALYTICS_ENABLED=true
VITE_ANALYTICS_KEY=analytics_key_here
```

**Important:** Never commit `.env.production` to version control!

---

## Post-Deployment Checklist

- [ ] Verify all pages load correctly
- [ ] Test claim submission flow
- [ ] Test claim status lookup
- [ ] Verify dark mode works
- [ ] Test on mobile devices
- [ ] Check console for errors
- [ ] Verify API calls are hitting correct endpoints
- [ ] Test file uploads
- [ ] Verify authentication flow
- [ ] Check analytics tracking (if enabled)
- [ ] Test form validation
- [ ] Verify responsive design on all breakpoints

---

## Performance Optimization

### 1. Enable Gzip Compression

Most hosting platforms enable this by default. For custom deployments:

**Nginx:**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

**Express:**
```javascript
const compression = require('compression');
app.use(compression());
```

### 2. Set Cache Headers

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Enable CDN

Use CloudFront (AWS), Cloudflare, or your hosting provider's CDN.

---

## Monitoring

### Error Tracking

Integrate Sentry:

```bash
npm install @sentry/react
```

```typescript
// In main.tsx
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: 'YOUR_SENTRY_DSN',
  environment: import.meta.env.MODE,
});
```

### Analytics

The app has analytics stubs ready. Integrate Google Analytics, Mixpanel, or similar:

```typescript
// Already implemented in services/api.ts
window.analytics?.track('event_name', { properties });
```

---

## Rollback Strategy

### Vercel/Netlify
- Go to Deployments → Select previous deployment → Promote to production

### Docker
```bash
docker pull easyairclaim-portal:previous-tag
docker-compose up -d
```

### S3
```bash
aws s3 sync s3://easyairclaim-portal-backup/ s3://easyairclaim-portal/
```

---

## Troubleshooting

### Issue: Blank page after deployment

**Solution:** Check browser console. Usually caused by:
1. Incorrect base URL in vite.config.ts
2. Missing environment variables
3. CORS issues

### Issue: 404 on refresh

**Solution:** Configure server to redirect all routes to index.html (SPA routing)

### Issue: API calls failing

**Solution:**
1. Verify VITE_API_BASE_URL is correct
2. Check CORS configuration on backend
3. Verify API key is valid

---

## Security Best Practices

1. **Never commit API keys** to version control
2. Use environment variables for all secrets
3. Enable HTTPS (SSL/TLS certificate)
4. Set appropriate CORS headers on backend
5. Implement Content Security Policy (CSP)
6. Use SRI (Subresource Integrity) for external scripts

---

## Support

For deployment issues, contact: easyairclaim@gmail.com
