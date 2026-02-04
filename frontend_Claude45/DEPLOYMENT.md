# Deployment Guide - ClaimPlane Portal

Complete guide for deploying the ClaimPlane frontend to various platforms.

## Pre-Deployment Checklist

- [ ] Backend API is deployed and accessible
- [ ] Environment variables configured
- [ ] API key obtained from backend
- [ ] Domain/subdomain ready (optional)
- [ ] SSL certificate configured (recommended)
- [ ] CORS configured on backend for frontend domain

## Environment Variables

All platforms require these environment variables:

```env
VITE_API_BASE_URL=https://api.claimplane.com/v1
VITE_API_KEY=your_production_api_key
VITE_ENV=production
```

---

## Vercel Deployment (Recommended)

### Via GitHub Integration

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/claimplane-frontend.git
   git push -u origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Configure:
     - Framework Preset: Vite
     - Root Directory: `./` (or `frontend/` if monorepo)
     - Build Command: `npm run build`
     - Output Directory: `dist`

3. **Set Environment Variables**
   - In Vercel dashboard → Settings → Environment Variables
   - Add all variables listed above
   - Apply to: Production, Preview, Development

4. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Future pushes to `main` will auto-deploy

### Via CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

**Custom Domain**:
- Vercel Dashboard → Domains → Add Domain
- Follow DNS configuration instructions

---

## Netlify Deployment

### Via Git Integration

1. **Push to GitHub** (same as Vercel)

2. **Create New Site**
   - Go to [netlify.com](https://netlify.com)
   - "Add new site" → "Import existing project"
   - Connect to GitHub

3. **Build Settings**
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Base directory: `frontend` (if monorepo)

4. **Environment Variables**
   - Site settings → Build & deploy → Environment
   - Add all variables

5. **Deploy**
   - Click "Deploy site"
   - Auto-deploys on git push

### Via CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Build locally
npm run build

# Deploy
netlify deploy --prod
```

**Custom Domain**:
- Site settings → Domain management → Add custom domain

---

## Docker Deployment

### 1. Create Dockerfile

Already included in project:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL
ARG VITE_API_KEY
ARG VITE_ENV
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_ENV=$VITE_ENV
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. Create nginx.conf

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1000;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 3. Build and Run

```bash
# Build image
docker build \
  --build-arg VITE_API_BASE_URL=https://api.claimplane.com/v1 \
  --build-arg VITE_API_KEY=your_api_key \
  --build-arg VITE_ENV=production \
  -t claimplane-frontend .

# Run container
docker run -d -p 80:80 --name claimplane-frontend claimplane-frontend

# Check logs
docker logs claimplane-frontend
```

### 4. Docker Compose (with backend)

```yaml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: http://backend:8000/v1
        VITE_API_KEY: ${API_KEY}
        VITE_ENV: production
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

---

## AWS S3 + CloudFront

### 1. Build Application

```bash
npm run build
```

### 2. Create S3 Bucket

```bash
aws s3 mb s3://claimplane-frontend
aws s3 website s3://claimplane-frontend \
  --index-document index.html \
  --error-document index.html
```

### 3. Upload Build

```bash
aws s3 sync dist/ s3://claimplane-frontend \
  --delete \
  --cache-control "public, max-age=31536000"
```

### 4. Create CloudFront Distribution

- Origin: S3 bucket endpoint
- Default root object: `index.html`
- Error pages: 404 → `/index.html` (for SPA routing)
- SSL certificate: Use ACM

### 5. Invalidate Cache on Deploy

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

---

## GitHub Pages

### 1. Install gh-pages

```bash
npm install -D gh-pages
```

### 2. Update package.json

```json
{
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
  },
  "homepage": "https://yourusername.github.io/claimplane"
}
```

### 3. Update vite.config.ts

```typescript
export default defineConfig({
  base: '/claimplane/',
  // ... rest of config
})
```

### 4. Deploy

```bash
npm run deploy
```

---

## DigitalOcean App Platform

1. **Connect Repository**
   - Create new app
   - Link GitHub repository

2. **Configure Build**
   - Build command: `npm run build`
   - Output directory: `dist`

3. **Environment Variables**
   - Add in app settings

4. **Deploy**
   - Automatic on git push

---

## Performance Optimization

### Enable Compression

Most platforms auto-enable, but verify:
- Gzip for text assets
- Brotli for modern browsers

### Configure Caching

```nginx
# nginx example
location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### CDN Configuration

- CloudFront, Cloudflare, or Fastly
- Cache static assets at edge
- Invalidate on deploy

---

## Monitoring & Analytics

### Add Google Analytics

```html
<!-- In index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Add Sentry (Error Tracking)

```bash
npm install @sentry/react
```

```typescript
// src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  environment: import.meta.env.VITE_ENV,
});
```

---

## SSL/HTTPS Configuration

### Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d claimplane.com -d www.claimplane.com
```

### Cloudflare (Free)

- Add domain to Cloudflare
- Enable SSL/TLS
- Set to "Full (strict)" mode

---

## Post-Deployment Verification

- [ ] Visit deployed URL
- [ ] Test all pages load correctly
- [ ] Submit test claim
- [ ] Check claim status lookup
- [ ] Test dark mode toggle
- [ ] Verify mobile responsiveness
- [ ] Check browser console for errors
- [ ] Test API connectivity
- [ ] Verify analytics tracking
- [ ] Check SSL certificate

---

## Rollback Procedure

### Vercel/Netlify

- Dashboard → Deployments → Previous deployment → Promote to production

### Docker

```bash
# Stop current
docker stop claimplane-frontend

# Run previous image
docker run -d -p 80:80 claimplane-frontend:previous-tag
```

### S3/CloudFront

- Restore previous S3 bucket version
- Invalidate CloudFront cache

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Build
        env:
          VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
          VITE_API_KEY: ${{ secrets.VITE_API_KEY }}
          VITE_ENV: production
        run: npm run build

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

---

## Troubleshooting

### Build Fails

```bash
# Clear cache
rm -rf node_modules dist package-lock.json
npm install
npm run build
```

### 404 on Refresh (SPA Routing)

Configure platform to serve `index.html` for all routes:

**Netlify** - Create `_redirects`:
```
/*    /index.html   200
```

**Vercel** - Create `vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### CORS Errors

- Backend must allow frontend domain
- Check `Access-Control-Allow-Origin` header

### Environment Variables Not Working

- Rebuild after changing env vars
- Verify prefix: `VITE_` is required

---

## Support

For deployment issues:
- Email: claimplane@gmail.com
- Check logs on your platform
- Review browser console for errors

**Ready to deploy? Start with Vercel for the fastest setup!**
