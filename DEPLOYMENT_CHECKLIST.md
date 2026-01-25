# Production Deployment Checklist

## Pre-Deployment Security Checklist

### ✅ Completed
- [x] Removed hardcoded credentials from docker-compose
- [x] Created production docker-compose.prod.yml
- [x] Added environment variable configuration
- [x] Implemented webhook signature verification
- [x] Restricted CORS in production mode
- [x] Disabled API docs in production
- [x] Added rate limiting middleware
- [x] Fixed race condition with SELECT FOR UPDATE
- [x] Added comprehensive health checks
- [x] Added error handling and logging
- [x] Added resource limits to containers

### ⚠️ Required Before Deployment

#### 1. Environment Variables Setup
```bash
# Generate strong secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For OTP_SECRET_KEY
openssl rand -hex 32  # For REDIS_PASSWORD
```

Create `.env.production` file with:
- Strong database password (min 32 chars)
- Strong Redis password (min 32 chars)
- Strong JWT secret (min 32 chars)
- Strong OTP secret (min 32 chars)
- Production CORS origins (comma-separated)
- Stripe webhook secret (if using Stripe)

#### 2. Database Setup
- [ ] Run migrations: `alembic upgrade head`
- [ ] Create database backup strategy
- [ ] Set up database monitoring
- [ ] Configure connection pooling limits

#### 3. Security Hardening
- [ ] Remove database/Redis port exposure (already done in prod compose)
- [ ] Set up firewall rules
- [ ] Configure SSL/TLS certificates
- [ ] Set up WAF (Web Application Firewall)
- [ ] Enable DDoS protection

#### 4. Monitoring & Observability
- [ ] Set up error tracking (Sentry recommended)
- [ ] Configure log aggregation (ELK, CloudWatch, etc.)
- [ ] Set up application metrics (Prometheus/Grafana)
- [ ] Configure alerting for critical errors
- [ ] Set up uptime monitoring

#### 5. Backup & Recovery
- [ ] Configure automated database backups
- [ ] Test backup restoration process
- [ ] Document disaster recovery procedures
- [ ] Set up backup retention policy

#### 6. Performance
- [ ] Load test the application
- [ ] Configure CDN for static assets
- [ ] Set up caching strategy
- [ ] Optimize database queries
- [ ] Configure auto-scaling (if using cloud)

#### 7. Documentation
- [ ] Document deployment process
- [ ] Document rollback procedure
- [ ] Document environment variables
- [ ] Create runbook for common issues

## Deployment Commands

### Initial Setup
```bash
# 1. Copy environment file
cp backend/.env.production.example backend/.env.production
# Edit with actual values

# 2. Build and start services
docker-compose -f docker-compose.prod.yml --env-file backend/.env.production up -d

# 3. Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# 4. Verify health
curl http://localhost:8000/health
```

### Updates
```bash
# 1. Pull latest code
git pull

# 2. Rebuild and restart
docker-compose -f docker-compose.prod.yml --env-file backend/.env.production up -d --build

# 3. Run new migrations (if any)
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Rollback
```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git checkout <previous-commit>

# 3. Restart
docker-compose -f docker-compose.prod.yml --env-file backend/.env.production up -d
```

## Post-Deployment Verification

- [ ] Health endpoint returns 200
- [ ] Database connection working
- [ ] Redis connection working
- [ ] Authentication flow working
- [ ] Payment webhook receiving events
- [ ] Celery workers processing tasks
- [ ] Logs are being generated
- [ ] No errors in application logs
- [ ] API response times acceptable
- [ ] Rate limiting working

## Security Audit Points

- [ ] No credentials in logs
- [ ] No sensitive data in error messages
- [ ] API docs not accessible
- [ ] CORS properly restricted
- [ ] Rate limiting active
- [ ] Webhook signatures verified
- [ ] Database not exposed publicly
- [ ] Redis not exposed publicly

