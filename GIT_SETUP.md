# Git Setup Guide - Safe Project Sharing

## ✅ Project Isolation Confirmed

**This project is completely isolated and will NOT affect your other projects.**

### Why It's Safe:
1. **Separate Directory**: All files are in `/Users/apple/mosab sport/` - isolated folder
2. **Docker Isolation**: Uses Docker containers - no system-wide installations
3. **Virtual Environments**: Python dependencies in containers only
4. **No Global Configs**: All configs are project-specific
5. **Git Ignore**: Proper `.gitignore` prevents committing sensitive files

---

## 🚀 Git Setup for Sharing Between Computers

### Step 1: Initialize Git Repository

```bash
cd "/Users/apple/mosab sport"

# Initialize git (if not already done)
git init

# Check current status
git status
```

### Step 2: Create .gitignore (Already Created)

The `.gitignore` file is already set up to exclude:
- Environment files (`.env`)
- Python cache (`__pycache__/`)
- Node modules (`node_modules/`)
- Uploads and generated files
- Database files
- Secrets and keys
- IDE files

### Step 3: Add Files to Git

```bash
# Add all files (respecting .gitignore)
git add .

# Check what will be committed
git status
```

### Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: Mosab Sport Platform - Phase 1 complete"
```

### Step 5: Create Remote Repository

**Option A: GitHub (Recommended)**
```bash
# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/mosab-sport.git
git branch -M main
git push -u origin main
```

**Option B: GitLab**
```bash
# Create a new repository on GitLab, then:
git remote add origin https://gitlab.com/YOUR_USERNAME/mosab-sport.git
git branch -M main
git push -u origin main
```

**Option C: Private Server**
```bash
# If you have your own Git server:
git remote add origin git@your-server.com:mosab-sport.git
git branch -M main
git push -u origin main
```

---

## 💻 Setting Up on Another Computer

### Step 1: Clone the Repository

```bash
# On the other computer
git clone https://github.com/YOUR_USERNAME/mosab-sport.git
cd mosab-sport
```

### Step 2: Create Environment File

```bash
# Copy example file
cp backend/.env.example backend/.env

# Edit with your values (if needed for local dev)
# For development, defaults in docker-compose.yml work
```

### Step 3: Start Services

```bash
# Build and start
docker-compose up -d --build

# Wait for services
sleep 30

# Run migrations
docker-compose exec api alembic upgrade head

# Seed demo data (optional)
python3 scripts/seed_demo_data.py
```

### Step 4: Verify

```bash
# Check health
curl http://localhost:8000/health

# Or run full test
make e2e
```

---

## 🔄 Daily Workflow

### On Computer 1 (Current)

```bash
# Make changes
# ... edit files ...

# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Description of changes"

# Push to remote
git push
```

### On Computer 2 (Other Computer)

```bash
# Pull latest changes
git pull

# Restart services if needed
docker-compose restart

# Or rebuild if dependencies changed
docker-compose up -d --build
```

---

## 🔒 Security Checklist

Before pushing to Git, verify:

- [ ] No `.env` files committed (check `git status`)
- [ ] No passwords/secrets in code
- [ ] No database files committed
- [ ] No uploads/user data committed
- [ ] `.gitignore` is working (run `git status` to verify)

### Verify Before First Push

```bash
# Check what will be committed
git status

# Review files (should NOT see):
# - .env files
# - __pycache__/
# - node_modules/
# - uploads/
# - *.db files
```

---

## 📋 Files That WILL Be Committed

✅ Safe to commit:
- Source code (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`)
- Configuration files (`.yml`, `.json`, `.ini`)
- Documentation (`.md`)
- Docker files (`Dockerfile`, `docker-compose.yml`)
- Scripts (`.sh`, `.py` in scripts/)
- Frontend source files

❌ Will NOT be committed (protected by .gitignore):
- `.env` files
- `__pycache__/`
- `node_modules/`
- `uploads/`
- Database files
- Logs
- IDE files

---

## 🛠️ Troubleshooting

### "Already a git repository"
```bash
# If you see this, git is already initialized
# Just add remote and push
git remote add origin <your-repo-url>
git push -u origin main
```

### "Files not being ignored"
```bash
# If .env or other files show up in git status:
# Remove them from git cache (but keep local files)
git rm --cached .env
git rm --cached -r __pycache__/

# Then commit the removal
git commit -m "Remove ignored files from git"
```

### "Merge conflicts on pull"
```bash
# If you have conflicts:
git pull
# Resolve conflicts in files
git add .
git commit -m "Resolve merge conflicts"
git push
```

### "Docker issues on other computer"
```bash
# Rebuild everything
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📦 Recommended Git Workflow

### Branch Strategy (Optional)

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push branch
git push -u origin feature/new-feature

# On GitHub/GitLab, create pull request
# After merge, update main branch:
git checkout main
git pull
```

### Commit Messages

Use clear, descriptive messages:
```bash
git commit -m "Add rate limiting middleware"
git commit -m "Fix race condition in booking endpoint"
git commit -m "Add E2E smoke test script"
```

---

## ✅ Final Verification

Before sharing:

1. ✅ Run `git status` - verify no sensitive files
2. ✅ Check `.gitignore` is working
3. ✅ Test locally - `make e2e` passes
4. ✅ Commit and push
5. ✅ Clone on other computer and verify it works

---

## 🎯 Quick Start Commands

```bash
# Initialize and push (first time)
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main

# On other computer
git clone <your-repo-url>
cd mosab-sport
docker-compose up -d --build
docker-compose exec api alembic upgrade head
```

---

## 🔐 Security Reminder

**NEVER commit:**
- `.env` files
- API keys
- Passwords
- Database files
- User uploads
- Private keys

**Always use:**
- `.env.example` for template
- Environment variables
- Secrets management (for production)
- `.gitignore` to protect files

---

Your project is **100% safe** and **ready to share**! 🚀

