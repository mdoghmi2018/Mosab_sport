# Quick Start Guide

## 🚀 First Time Setup

### 1. Start the Application

```bash
cd "/Users/apple/mosab sport"
docker-compose up -d --build
```

### 2. Wait for Services (30 seconds)

```bash
sleep 30
```

### 3. Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 4. Seed Demo Data

```bash
python3 scripts/seed_demo_data.py
```

### 5. Verify Everything Works

```bash
# Check health
curl http://localhost:8000/health

# Or run full test
make e2e
```

---

## 📦 Git Setup (One Time)

### Initialize Git

```bash
# Check if already initialized
git status

# If not, initialize
git init

# Add all files
git add .

# Check what will be committed (verify no .env files)
git status

# Commit
git commit -m "Initial commit: Mosab Sport Platform"
```

### Push to Remote

```bash
# Create repository on GitHub/GitLab first, then:
git remote add origin https://github.com/YOUR_USERNAME/mosab-sport.git
git branch -M main
git push -u origin main
```

---

## 💻 On Another Computer

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/mosab-sport.git
cd mosab-sport

# Start
docker-compose up -d --build

# Migrate
docker-compose exec api alembic upgrade head

# Test
make e2e
```

---

## ✅ Project Safety

**This project is 100% isolated:**
- ✅ Won't affect other projects
- ✅ All dependencies in Docker
- ✅ No system-wide changes
- ✅ Safe to share via Git

---

## 🎯 Common Commands

```bash
make help          # Show all commands
make up            # Start services
make down          # Stop services
make logs          # View logs
make health        # Check API health
make seed          # Seed demo data
make test          # Run E2E test
make e2e           # Full golden routine
```

---

## 📚 Documentation

- `README.md` - Main documentation
- `GIT_SETUP.md` - Detailed Git guide
- `FINAL_AUDIT_REPORT.md` - Complete audit
- `scripts/README.md` - Script documentation

---

**You're all set! 🎉**

