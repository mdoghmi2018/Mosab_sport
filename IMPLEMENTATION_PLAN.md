# Implementation Plan - UI Workflow Alignment

## 📊 Current State vs UI Requirements

Based on the UI screenshots, here's what needs to be implemented:

---

## 🔴 **CRITICAL MISSING FEATURES**

### 1. **Event Organization Workflow (8-Step Process)**

**Current:** Basic booking flow (venue → court → slot → reservation)

**Required:** Unified "Organize Event" endpoint that handles:
- Sport selection
- Match format (5x5, 6x6, 7x7, 8x8, 9x9, 10x10, 11x11)
- Event type (Single Match, Friendly, Tournament, Training)
- Event details (date, time, recurring, court selection)
- Player import
- Formation builder
- Add-ons selection
- Review & submit with approval

**Action Items:**
- [ ] Create `Event` model (separate from Match)
- [ ] Add `EventType` enum
- [ ] Add `MatchFormat` enum
- [ ] Create `/api/v1/events/organize` endpoint
- [ ] Add approval workflow

---

### 2. **Match Format & Player Count**

**Current:** Match model has `sport` but no format

**Required:**
- Match format field (5x5, 8x8, etc.)
- Player count per team
- Total players tracking

**Action Items:**
- [ ] Add `format` field to Match model (e.g., "8x8")
- [ ] Add `players_per_team` field
- [ ] Add `total_players` field
- [ ] Update migration

---

### 3. **Event Types**

**Current:** No event type distinction

**Required:**
- Single Match (one-time or recurring)
- Friendly Match (referee mandatory)
- Tournament (multi-team, bracket)
- Training Session (1-on-1, group, morning)

**Action Items:**
- [ ] Create `EventType` enum
- [ ] Add `event_type` to Match/Event model
- [ ] Add tournament-specific fields if needed
- [ ] Add training session type handling

---

### 4. **Add-ons System**

**Current:** No add-ons support

**Required:**
- Referee ($50)
- Commentator ($75)
- Media Coverage ($150)
- Match Recording ($100)
- Live Streaming ($200)
- Ceremony Stage ($300)
- Fireworks ($500)
- Medals & Trophies ($120)
- Jerseys & Kits ($250)
- Custom Add-on

**Action Items:**
- [ ] Create `Addon` model
- [ ] Create `EventAddon` junction table
- [ ] Add add-ons to booking/event creation
- [ ] Calculate total with add-ons
- [ ] Store add-ons in payment

---

### 5. **Recurring Events**

**Current:** Reservation model doesn't support recurring

**Required:**
- Daily recurring
- Weekly recurring
- Pattern storage

**Action Items:**
- [ ] Add `is_recurring` boolean to Reservation
- [ ] Add `recurrence_pattern` JSONB field
- [ ] Add `recurrence_end_date` field
- [ ] Create background job to generate recurring slots

---

### 6. **Own Court Option**

**Current:** Only venue/court selection

**Required:**
- "I have my own court" option
- Custom venue creation in booking flow

**Action Items:**
- [ ] Add `use_own_court` boolean to Reservation
- [ ] Add `custom_venue_json` field
- [ ] Update booking endpoint to handle own court

---

### 7. **Player Import & AI**

**Current:** Placeholder in formation.py

**Required:**
- Paste player names and jersey numbers
- AI extraction of players
- Auto-generate teams
- Auto-create formation

**Action Items:**
- [ ] Create `/api/v1/players/import` endpoint
- [ ] Implement basic parsing (regex for now, AI later)
- [ ] Auto-split into teams
- [ ] Auto-generate formation positions

---

### 8. **Formation Builder Enhancement**

**Current:** Basic formation creation exists

**Required:**
- Drag-and-drop position updates
- Team A and Team B support
- Share lineup functionality (exists but needs enhancement)

**Action Items:**
- [ ] Add `PATCH /formations/{formation_id}/positions` endpoint
- [ ] Support multiple teams in formation
- [ ] Enhance share token functionality

---

### 9. **Public Matches**

**Current:** No public matches

**Required:**
- Browse public/open matches
- Join match functionality
- Filter by format, date, location

**Action Items:**
- [ ] Add `is_public` boolean to Match
- [ ] Add `spots_available` field
- [ ] Create `/api/v1/matches/public` endpoint
- [ ] Create `/api/v1/matches/{match_id}/join` endpoint
- [ ] Add player registration to match

---

### 10. **Wallet System**

**Current:** No wallet model

**Required:**
- Wallet balance
- Transaction history
- Payment methods storage
- Add funds / Withdraw

**Action Items:**
- [ ] Create `Wallet` model
- [ ] Create `Transaction` model
- [ ] Create `PaymentMethod` model
- [ ] Create wallet endpoints
- [ ] Integrate with payment system

---

### 11. **User Stats**

**Current:** Basic user model

**Required:**
- Events count
- Wins count
- Friends count
- Rating

**Action Items:**
- [ ] Add stats fields to User model (or separate UserStats)
- [ ] Create stats calculation logic
- [ ] Create `/api/v1/users/me/stats` endpoint

---

### 12. **Dashboard/Home Endpoints**

**Current:** No dashboard data

**Required:**
- Events this month
- Active bookings
- Matches played
- Featured matches
- Upcoming bookings with details

**Action Items:**
- [ ] Create `/api/v1/dashboard/stats` endpoint
- [ ] Create `/api/v1/dashboard/upcoming-bookings` endpoint
- [ ] Create `/api/v1/dashboard/featured-matches` endpoint

---

### 13. **Approval Workflow**

**Current:** Direct booking

**Required:**
- Event submission for approval
- Admin approval endpoint
- Payment after approval

**Action Items:**
- [ ] Add `status` to Event (draft, pending_approval, approved, rejected)
- [ ] Create approval endpoints
- [ ] Update payment flow to require approval first

---

## 📋 **Implementation Order**

### **Phase 1: Core Event Organization (Priority 1)**
1. Add EventType and MatchFormat enums
2. Create Event model
3. Add recurring events support
4. Create unified Organize Event endpoint

### **Phase 2: Enhanced Features (Priority 2)**
5. Add-ons system
6. Player import
7. Formation builder enhancement
8. Own court option

### **Phase 3: Social & Discovery (Priority 3)**
9. Public matches
10. Join match functionality
11. User stats

### **Phase 4: Wallet & Payments (Priority 4)**
12. Wallet system
13. Transaction history

### **Phase 5: Dashboard (Priority 5)**
14. Dashboard endpoints
15. Stats aggregation

---

## 🎯 **Next Steps**

1. **Review this plan**
2. **Start with Phase 1** (Core Event Organization)
3. **Create database migrations**
4. **Update API endpoints**
5. **Test with UI flow**

---

**Ready to start implementation!** 🚀

