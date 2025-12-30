# Technical Debt & Infrastructure

[← Back to Roadmap](README.md)

---

**Status**: 🔧 **ONGOING MAINTENANCE**
**Priority**: VARIES - Some critical, some nice-to-have
**Timeline**: Continuous improvement

This document tracks technical debt, infrastructure improvements, and maintenance tasks that need attention.

---


These should be addressed alongside feature development:

### Database Migrations
- [ ] Set up Alembic properly
- [ ] Remove `create_all()` from lifespan manager
- [ ] Create initial migration from current schema
- [ ] Document migration process

### Testing
- [ ] Increase test coverage to 80%+
- [ ] Add integration tests for all new features
- [ ] Set up continuous testing with pytest-watch
- [ ] Performance testing for file upload/download

### CI/CD
- [ ] Set up GitHub Actions or GitLab CI
- [ ] Automated testing on pull requests
- [ ] Automated deployment to staging
- [ ] Code quality checks (black, pylint, mypy)

### Monitoring & Logging
- [ ] Structured logging with JSON format
- [ ] Centralized log aggregation (ELK stack or CloudWatch)
- [ ] Application performance monitoring (New Relic, DataDog)
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring

### Documentation
- [ ] API documentation with examples
- [ ] Admin user guide
- [ ] Customer user guide
- [ ] Developer onboarding guide
- [ ] Deployment guide

---

## Notes for Future Claude Sessions

---

[← Back to Roadmap](README.md)
