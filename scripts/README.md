# Verification Scripts

## Quick Start

```bash
# Full golden routine (bring-up + seed + E2E test)
make e2e

# Or step by step:
make build          # Start services
make migrate        # Run migrations
make seed           # Seed demo data
make test           # Run E2E smoke test
```

## Scripts

### `golden_routine.sh`
Brings up the stack, verifies services, runs migrations, and checks health.

**Usage:**
```bash
./scripts/golden_routine.sh
```

**What it does:**
1. Starts Docker stack
2. Checks service status
3. Verifies logs for errors
4. Applies migrations
5. Checks API health
6. Verifies API docs
7. Checks frontend port
8. Verifies Celery beat
9. Checks shared volumes

### `seed_demo_data.py`
Creates minimal demo data for testing:
- 1 Venue (Demo Sports Complex)
- 1 Court (Court 1, football)
- 15 Slots (3 per day for 5 days)
- 1 Organizer user (+1234567890)
- 1 Referee user (+1234567891)

**Usage:**
```bash
python3 scripts/seed_demo_data.py
# or
docker-compose exec api python3 /app/scripts/seed_demo_data.py
```

### `e2e_smoke_test.py`
End-to-end smoke test covering the complete Phase 1 flow:
1. Authentication (organizer + referee)
2. Booking (list venues → courts → slots → create reservation)
3. Payment initiation
4. Webhook simulation (with idempotency test)
5. Match creation
6. Referee flow (accept → start)
7. Match events (with sequence enforcement test)
8. Match finalization
9. Report generation

**Usage:**
```bash
python3 scripts/e2e_smoke_test.py
```

**Requirements:**
- Services must be running
- Demo data must be seeded
- OTP must be available (via `/auth/dev-otp` endpoint or manual input)

## Common Issues Fixed

### 1. ✅ Frontend Port Mismatch
- Vite explicitly configured to use port 3000 (matches docker-compose)

### 2. ✅ OTP Observable in Dev
- OTP logged to console in development mode
- Dev endpoint `/auth/dev-otp` for testing

### 3. ✅ Report PDF Path Shared
- Volume `./backend/uploads` mounted in both API and worker containers

### 4. ✅ Hold TTL Expiry Running
- Celery beat service added to docker-compose
- Task scheduled to run every minute

### 5. ✅ Webhook Signature Verification
- Supports dev mode (can bypass if no secret configured)
- Proper signature verification when secret is set

### 6. ✅ Race Condition Fixed
- `SELECT FOR UPDATE` used in booking endpoint
- Prevents double-booking under concurrency

## Testing the Golden Path

```bash
# 1. Start everything
make build

# 2. Wait for services (30s)
sleep 30

# 3. Run golden routine
./scripts/golden_routine.sh

# 4. Seed data
make seed

# 5. Run E2E test
make test
```

## Expected Output

### Golden Routine
- ✅ All services running
- ✅ Migrations applied
- ✅ Health check passing
- ✅ API docs accessible
- ✅ Celery beat running

### E2E Test
- ✅ Organizer authenticated
- ✅ Referee authenticated
- ✅ Reservation created
- ✅ Payment initiated
- ✅ Webhook processed (idempotent)
- ✅ Match created
- ✅ Match started
- ✅ Events added (sequence enforced)
- ✅ Match finalized
- ✅ Report generated

## Troubleshooting

### OTP Not Available
If OTP endpoint doesn't work, check API logs:
```bash
docker-compose logs api | grep OTP
```

Or manually input OTP when prompted by test script.

### Services Not Starting
Check logs:
```bash
docker-compose logs
```

### Migration Failures
Reset database (WARNING: deletes all data):
```bash
make clean
make build
make migrate
```

### Report Not Generating
Check worker logs:
```bash
docker-compose logs worker
```

Verify shared volume:
```bash
docker-compose exec api ls -la /app/uploads/reports
docker-compose exec worker ls -la /app/uploads/reports
```

