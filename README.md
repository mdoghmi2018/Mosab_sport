# Mosab Sport Platform

A comprehensive sports platform for booking courts, managing matches, live scoring, and generating reports.

## Features

### Phase 1 (Core)
- **Booking System**: Venue/court booking with slot management and reservation holds
- **Payment Integration**: Payment processing with webhook idempotency
- **Match Operations**: Match creation, referee assignment, live event tracking
- **Report Generation**: Automated PDF report generation with checksums

### Phase 2 (v1.2 Enhancements)
- **Awards**: Man of the match and best goal awards
- **Personal Training**: PT request system and inbox
- **Formations**: Squad management and formation sharing
- **Advertising**: Ad approval workflow and placement system

## Architecture

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Workers**: Celery
- **Frontend**: React + Vite + Tailwind CSS
- **Containerization**: Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Setup

1. **Clone and navigate to the project**
```bash
cd "mosab sport"
```

2. **Create environment file**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec api alembic upgrade head
```

5. **Access the application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Project Structure

```
mosab sport/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API routes
│   │   ├── core/          # Core utilities (config, database, security)
│   │   ├── models/        # SQLAlchemy models
│   │   └── tasks/         # Celery tasks
│   ├── alembic/           # Database migrations
│   └── requirements.txt
├── frontend/              # React frontend (to be added)
└── docker-compose.yml
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/start` - Start authentication (send OTP)
- `POST /api/v1/auth/verify` - Verify OTP and get JWT

### Booking
- `GET /api/v1/venues` - List venues
- `GET /api/v1/venues/{venue_id}/courts` - List courts
- `GET /api/v1/venues/courts/{court_id}/slots` - List available slots
- `POST /api/v1/venues/reservations` - Create reservation
- `GET /api/v1/venues/reservations/my` - Get my reservations

### Payments
- `POST /api/v1/payments/initiate` - Initiate payment
- `POST /api/v1/payments/webhook` - Payment webhook

### Match Operations
- `POST /api/v1/matches/from-reservation/{reservation_id}` - Create match
- `POST /api/v1/matches/{match_id}/referee/offer` - Offer referee
- `POST /api/v1/matches/{match_id}/referee/accept` - Accept assignment
- `POST /api/v1/matches/{match_id}/start` - Start match
- `POST /api/v1/matches/{match_id}/events` - Add match event
- `POST /api/v1/matches/{match_id}/finalize` - Finalize match
- `GET /api/v1/matches/{match_id}/events` - Get match events

### Reports
- `POST /api/v1/reports/matches/{match_id}/generate` - Generate report
- `GET /api/v1/reports/matches/{match_id}/report` - Download report

## Development

### Running Migrations
```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1
```

### Running Tests
```bash
docker-compose exec api pytest
```

### Accessing Services
```bash
# PostgreSQL
docker-compose exec db psql -U mosab_user -d mosab_sport

# Redis CLI
docker-compose exec redis redis-cli

# Celery Worker Logs
docker-compose logs -f worker
```

## Environment Variables

See `backend/.env.example` for required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - JWT signing key
- `OTP_SECRET_KEY` - OTP generation key

## License

Proprietary - All rights reserved

