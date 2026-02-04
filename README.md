# ClaimPlane - Flight Compensation Platform

FastAPI-based flight compensation claim management platform with EU261/2004 calculation, admin dashboard, async email notifications, and secure file storage.

**Current Version:** v0.2.0 (Phase 2 Complete - Email Notifications & Async Processing)

---

## 🚀 Quick Start - Complete System

### Prerequisites
- Docker & Docker Compose
- Node.js 18+

### Start Everything (3 Commands)

```bash
# 1. Start backend services (API, database, Redis, Celery worker)
docker-compose up -d

# 2. Start frontend dev server (in a new terminal)
cd frontend_Claude45
npm run dev

# 3. Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Admin:    http://localhost:3000/admin
```

**That's it!** The system is now running.

---

## 📦 What's Running

| Service | Port | Description |
|---------|------|-------------|
| Frontend (Vite) | 3000 | React customer portal |
| Backend API | 8000 | FastAPI server |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Task queue broker |
| Celery Worker | - | Background tasks |

---

## 🔧 Development Workflow

### Making Frontend Changes
The Vite dev server has hot reload - changes appear instantly at http://localhost:3000

### Making Backend Changes
```bash
# Restart API container
docker-compose restart api

# Or run locally (requires conda environment)
source ~/miniconda3/bin/activate ClaimPlane
python app/main.py
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
```

---

## 🧪 Testing

```bash
# Backend tests (activate conda environment first)
source ~/miniconda3/bin/activate ClaimPlane
pytest

# Frontend tests
cd frontend_Claude45
npm test
```

---

## 🏗️ Project Status

**✅ Completed Phases:**
- Phase 1: Admin Dashboard & Claim Workflow
- Phase 2: Email Notifications & Async Processing

**🚧 Next Priority:**
- Phase 3: JWT Authentication & Authorization System

See [ROADMAP.md](ROADMAP.md) for complete development plan.

---

## 📁 Key Files & Documentation

- **[CLAUDE.md](CLAUDE.md)** - Project architecture and development guide
- **[ROADMAP.md](ROADMAP.md)** - Development priorities and phases
- **[DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)** - Environment setup
- **[docs/](docs/)** - Detailed technical documentation

---

## 🛠️ Tech Stack

**Backend:** FastAPI, PostgreSQL, SQLAlchemy 2.0, Celery, Redis
**Frontend:** React, TypeScript, Vite, TailwindCSS
**Security:** Fernet encryption, JWT (Phase 3), bcrypt
**Infrastructure:** Docker, nginx, Nextcloud (WebDAV)

---

## 🔒 Security Notes

⚠️ **Current MVP uses header-based auth (X-Customer-ID)** - Phase 3 will replace with JWT authentication.

See [docs/SECURITY_AUDIT_v0.2.0.md](docs/SECURITY_AUDIT_v0.2.0.md) for security audit.

---

## 📞 Support

**Email:** support@claimplane.com

**Issues:** Report bugs on GitHub repository

---

## 📄 License

Private - All rights reserved.

---

**Built for EU261/2004 flight compensation claims**
