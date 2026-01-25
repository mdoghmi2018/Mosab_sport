#!/usr/bin/env python3
"""
Seed Demo Data Script
Creates minimal data for end-to-end testing:
- 1 Venue
- 1 Court
- 5 Slots (next 5 days)
- 1 Organizer User
- 1 Referee User
"""

import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.models.venue import Venue, Court, Slot, SlotStatus
from app.core.database import Base

def seed_data():
    """Seed minimal demo data"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding demo data...")
        
        # Create organizer user
        organizer = db.query(User).filter(User.phone == "+1234567890").first()
        if not organizer:
            organizer = User(
                phone="+1234567890",
                email="organizer@demo.com",
                name="Demo Organizer",
                role=UserRole.ORGANIZER,
                verified_phone=True,
                verified_email=True
            )
            db.add(organizer)
            print("✅ Created organizer user")
        else:
            print("ℹ️  Organizer user already exists")
        
        # Create referee user
        referee = db.query(User).filter(User.phone == "+1234567891").first()
        if not referee:
            referee = User(
                phone="+1234567891",
                email="referee@demo.com",
                name="Demo Referee",
                role=UserRole.REFEREE,
                verified_phone=True,
                verified_email=True
            )
            db.add(referee)
            print("✅ Created referee user")
        else:
            print("ℹ️  Referee user already exists")
        
        db.commit()
        db.refresh(organizer)
        db.refresh(referee)
        
        # Create venue
        venue = db.query(Venue).filter(Venue.name == "Demo Sports Complex").first()
        if not venue:
            venue = Venue(
                name="Demo Sports Complex",
                location_json={
                    "address": "123 Sports Street",
                    "city": "Demo City",
                    "coordinates": {"lat": 40.7128, "lng": -74.0060}
                },
                owner_user_id=organizer.id,
                policies_json={
                    "cancellation_policy": "24 hours notice required",
                    "refund_policy": "Full refund if cancelled 24h before"
                }
            )
            db.add(venue)
            print("✅ Created venue")
        else:
            print("ℹ️  Venue already exists")
        
        db.commit()
        db.refresh(venue)
        
        # Create court
        court = db.query(Court).filter(
            Court.venue_id == venue.id,
            Court.name == "Court 1"
        ).first()
        
        if not court:
            court = Court(
                venue_id=venue.id,
                name="Court 1",
                sport="football",
                attributes_json={
                    "surface": "artificial_grass",
                    "size": "full",
                    "amenities": ["lights", "parking"]
                }
            )
            db.add(court)
            print("✅ Created court")
        else:
            print("ℹ️  Court already exists")
        
        db.commit()
        db.refresh(court)
        
        # Create slots for next 5 days
        now = datetime.utcnow()
        slots_created = 0
        
        for day in range(5):
            slot_date = now + timedelta(days=day)
            
            # Create 3 slots per day (morning, afternoon, evening)
            for hour in [10, 14, 18]:
                start_ts = slot_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                end_ts = start_ts + timedelta(hours=2)
                
                # Check if slot already exists
                existing = db.query(Slot).filter(
                    Slot.court_id == court.id,
                    Slot.start_ts == start_ts,
                    Slot.end_ts == end_ts
                ).first()
                
                if not existing:
                    slot = Slot(
                        court_id=court.id,
                        start_ts=start_ts,
                        end_ts=end_ts,
                        price_cents=5000,  # $50.00
                        currency="USD",
                        status=SlotStatus.OPEN
                    )
                    db.add(slot)
                    slots_created += 1
        
        db.commit()
        print(f"✅ Created {slots_created} slots")
        
        # Print summary
        print("\n📊 Demo Data Summary:")
        print(f"   Venue ID: {venue.id}")
        print(f"   Court ID: {court.id}")
        print(f"   Organizer Phone: +1234567890")
        print(f"   Referee Phone: +1234567891")
        print(f"   Total Slots: {slots_created}")
        print("\n✅ Seeding complete!")
        
        return {
            "venue_id": str(venue.id),
            "court_id": str(court.id),
            "organizer_phone": "+1234567890",
            "referee_phone": "+1234567891"
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

